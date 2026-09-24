import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.db.models import Message, Conversation
from backend.app.schemas.schemas import AdvisoryQueryRequest, AdvisoryQueryResponse, StructuredQueryInfo
from backend.app.core.asr_engine import asr_engine
from backend.app.core.query_understanding import query_understanding_engine
from backend.app.core.context_engine import context_engine
from backend.app.core.safety_gate import pre_safety_gate
from backend.app.core.retrieval_engine import retrieval_engine
from backend.app.core.reranker import reranker
from backend.app.core.grounding_gate import grounding_gate
from backend.app.core.llm_generator import llm_generator
from backend.app.core.claim_verifier import claim_verifier
from backend.app.core.confidence_engine import confidence_engine
from backend.app.core.escalation_engine import escalation_engine
from backend.app.core.translation_engine import translation_engine
from backend.app.core.tts_engine import tts_engine
from backend.app.core.audit_logger import audit_logger

router = APIRouter(prefix="/advisory", tags=["advisory"])

@router.post("/query", response_model=AdvisoryQueryResponse)
async def process_advisory_query(
    req: AdvisoryQueryRequest,
    db: Session = Depends(get_db)
):
    query_id = f"QRY-{uuid.uuid4().hex[:8].upper()}"

    # 1. ASR & Transcript Normalization
    transcript, detected_lang, asr_conf = await asr_engine.transcribe(
        req.text, req.audio_base64, req.language
    )
    audit_logger.log_event(db, query_id, "ASR_COMPLETED", {"transcript": transcript, "lang": detected_lang})

    # 2. Query Understanding
    nlp_res = query_understanding_engine.parse_query(transcript, req.crop_override)
    structured_info = StructuredQueryInfo(
        intent=nlp_res["intent"],
        crop=nlp_res["crop"],
        symptoms=nlp_res["symptoms"],
        chemicals_mentioned=nlp_res["chemicals_mentioned"],
        urgency=nlp_res["urgency"]
    )

    # 3. Context Engine (with multi-turn dialogue memory resolution)
    ctx = await context_engine.resolve_context(
        farmer_id=req.farmer_id or "FARM-1001",
        crop=nlp_res["crop"],
        crop_stage_days=req.crop_stage_days,
        district=req.location_district,
        state=req.location_state,
        db=db,
        conversation_id=req.conversation_id
    )

    # 4. Pre-Safety Gate
    pre_safe, risk_lvl, pre_reason = pre_safety_gate.evaluate(transcript, nlp_res, ctx)
    if not pre_safe:
        audit_logger.log_event(db, query_id, "PRE_SAFETY_REJECTED", {"reason": pre_reason})
        
        esc_id = escalation_engine.create_escalation(
            db, req.farmer_id or "FARM-1001", query_id, transcript,
            nlp_res["crop"], ctx["district"], risk_lvl, pre_reason, []
        )
        
        fallback_msg = (
            "आपला प्रश्न उच्च जोखीम किंवा अपुऱ्या माहितीचा आहे. "
            "सुरक्षिततेसाठी आमचे कृषी तज्ञ आपल्याशी लवकरच संपर्क साधतील."
        ) if detected_lang == "mr" else "आपका प्रश्न सुरक्षा नीति के अंतर्गत विशेषज्ञ समीक्षा के लिए भेज दिया गया है।"

        return AdvisoryQueryResponse(
            query_id=query_id,
            status="ESCALATED_TO_EXPERT",
            language_detected=detected_lang,
            structured_query=structured_info,
            answer_text=fallback_msg,
            audio_url=await tts_engine.synthesize(query_id, fallback_msg, detected_lang),
            confidence_score=0.2,
            confidence_level="LOW",
            grounding_status="INSUFFICIENT",
            safety_status="FAILED",
            retrieved_evidence=[],
            claims_verified=[],
            escalation_id=esc_id
        )

    # 5. Hybrid Retrieval
    candidates = retrieval_engine.retrieve(db, transcript, ctx["crop"], ctx["district"])
    
    # 6. Reranking
    reranked_evidence = reranker.rerank(candidates, ctx["crop"], ctx["stage_days"], ctx["district"])
    audit_logger.log_event(db, query_id, "RETRIEVAL_COMPLETED", {"count": len(reranked_evidence)})

    # 7. Grounding Gate
    ground_status, ground_reason = grounding_gate.evaluate_grounding(reranked_evidence, nlp_res["intent"], risk_lvl)
    
    if ground_status != "SUPPORTED":
        audit_logger.log_event(db, query_id, "GROUNDING_FAILED", {"reason": ground_reason})
        esc_id = escalation_engine.create_escalation(
            db, req.farmer_id or "FARM-1001", query_id, transcript,
            ctx["crop"], ctx["district"], risk_lvl, f"GROUNDING_{ground_status}", reranked_evidence
        )
        esc_msg = (
            "या प्रश्नावर आमच्याकडे पूर्णपणे पडताळलेला पुरावा उपलब्ध नाही. "
            "चुकीचा सल्ला टाळण्यासाठी ही केस आमच्या कृषी तज्ञांकडे वर्ग केली आहे."
        )
        return AdvisoryQueryResponse(
            query_id=query_id,
            status="ESCALATED_TO_EXPERT",
            language_detected=detected_lang,
            structured_query=structured_info,
            answer_text=esc_msg,
            audio_url=await tts_engine.synthesize(query_id, esc_msg, detected_lang),
            confidence_score=0.3,
            confidence_level="LOW",
            grounding_status=ground_status,
            safety_status="PASSED",
            retrieved_evidence=reranked_evidence,
            claims_verified=[],
            escalation_id=esc_id
        )

    # 8. Grounded LLM Response Generation (with dialogue history)
    raw_answer = await llm_generator.generate_response(
        transcript, reranked_evidence, ctx["crop"], ctx["stage_name"],
        ctx["weather"]["condition"], detected_lang, ctx.get("conversation_history")
    )


    # 9. Claim Extraction & Post-LLM Safety Verification
    claims_list, claims_passed = claim_verifier.verify_claims(raw_answer, reranked_evidence)
    
    # 10. Multi-Factor Confidence Score
    conf_score, conf_level = confidence_engine.calculate_confidence(
        reranked_evidence, ground_status, claims_passed, asr_conf
    )

    # 11. Final Decisioning
    if conf_level == "LOW" or not claims_passed:
        esc_id = escalation_engine.create_escalation(
            db, req.farmer_id or "FARM-1001", query_id, transcript,
            nlp_res["crop"], ctx["district"], risk_lvl, "POST_SAFETY_UNSUPPORTED_CLAIM", reranked_evidence
        )
        return AdvisoryQueryResponse(
            query_id=query_id,
            status="ESCALATED_TO_EXPERT",
            language_detected=detected_lang,
            structured_query=structured_info,
            answer_text="उत्तर अचूक नसल्याच्या शंकेमुळे ही माहिती तज्ञांच्या तपासणीसाठी पाठवण्यात आली आहे.",
            audio_url=None,
            confidence_score=conf_score,
            confidence_level=conf_level,
            grounding_status=ground_status,
            safety_status="FAILED" if not claims_passed else "PASSED",
            retrieved_evidence=reranked_evidence,
            claims_verified=claims_list,
            escalation_id=esc_id
        )

    # 12. Translation Layer
    translated_answer = await translation_engine.translate(raw_answer, detected_lang)

    # 13. TTS Synthesis
    audio_url = await tts_engine.synthesize(query_id, translated_answer, detected_lang)
    audit_logger.log_event(db, query_id, "PIPELINE_SUCCESS", {"confidence": conf_score})

    return AdvisoryQueryResponse(
        query_id=query_id,
        status="ANSWERED",
        language_detected=detected_lang,
        structured_query=structured_info,
        answer_text=translated_answer,
        audio_url=audio_url,
        confidence_score=conf_score,
        confidence_level=conf_level,
        grounding_status="SUPPORTED",
        safety_status="PASSED",
        retrieved_evidence=reranked_evidence,
        claims_verified=claims_list,
        escalation_id=None
    )
