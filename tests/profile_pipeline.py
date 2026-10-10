#!/usr/bin/env python3
"""
FasalMitra Comprehensive Pipeline Latency Profiler
Instruments and benchmarks every single stage of the Advisory API pipeline
to identify exact bottlenecks and time consumers.
"""

import sys
import os
import time
import asyncio
import uuid
from typing import Dict, Any, List

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.db.database import SessionLocal
from backend.app.schemas.schemas import AdvisoryQueryRequest, StructuredQueryInfo
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
from backend.app.core.translation_engine import translation_engine
from backend.app.core.tts_engine import tts_engine
from backend.app.core.audit_logger import audit_logger


async def profile_single_query(query_text: str, crop: str = "Cotton", language: str = "en") -> Dict[str, Any]:
    db = SessionLocal()
    query_id = f"PROF-{uuid.uuid4().hex[:6].upper()}"
    stages = {}
    total_start = time.perf_counter()

    print(f"\n" + "=" * 80)
    print(f"  PROFILING QUERY: \"{query_text}\" (Crop: {crop}, Lang: {language})")
    print("=" * 80)

    # 1. ASR & Transcript Normalization
    t0 = time.perf_counter()
    transcript, detected_lang, asr_conf = await asr_engine.transcribe(query_text, None, language)
    stages["1. ASR Engine (transcribe)"] = (time.perf_counter() - t0) * 1000

    # 2. Query Understanding NLP
    t0 = time.perf_counter()
    nlp_res = query_understanding_engine.parse_query(transcript, crop)
    stages["2. Query Understanding (NLP)"] = (time.perf_counter() - t0) * 1000

    # 3. Context Engine
    t0 = time.perf_counter()
    ctx = await context_engine.resolve_context(
        farmer_id="FARM-1001",
        crop=nlp_res["crop"],
        crop_stage_days=35,
        district="Latur",
        state="Maharashtra",
        db=db,
        conversation_id=None
    )
    stages["3. Context Engine (Profile+Weather)"] = (time.perf_counter() - t0) * 1000

    # 4. Pre-Safety Gate
    t0 = time.perf_counter()
    pre_safe, risk_lvl, pre_reason = pre_safety_gate.evaluate(transcript, nlp_res, ctx)
    stages["4. Pre-Safety Gate"] = (time.perf_counter() - t0) * 1000

    # 5. Hybrid Retrieval
    t0 = time.perf_counter()
    candidates = retrieval_engine.retrieve(db, transcript, ctx["crop"], ctx["district"])
    stages["5. Hybrid Retrieval (SQL/DB)"] = (time.perf_counter() - t0) * 1000

    # 6. Reranker
    t0 = time.perf_counter()
    reranked_evidence = reranker.rerank(candidates, ctx["crop"], ctx["stage_days"], ctx["district"])
    stages["6. Reranker (Semantic/Stage)"] = (time.perf_counter() - t0) * 1000

    # 7. Grounding Gate
    t0 = time.perf_counter()
    ground_status, ground_reason = grounding_gate.evaluate_grounding(reranked_evidence, nlp_res["intent"], risk_lvl)
    stages["7. Grounding Gate"] = (time.perf_counter() - t0) * 1000

    # 8. Grounded LLM Response Generation
    t0 = time.perf_counter()
    raw_answer = await llm_generator.generate_response(
        transcript, reranked_evidence, ctx["crop"], ctx["stage_name"],
        ctx["weather"]["condition"], detected_lang, ctx.get("conversation_history")
    )
    stages["8. LLM Generator (Gemini/Fallback)"] = (time.perf_counter() - t0) * 1000

    # 9. Claim Extraction & Verification
    t0 = time.perf_counter()
    claims_list, claims_passed = claim_verifier.verify_claims(raw_answer, reranked_evidence)
    stages["9. Claim Verifier"] = (time.perf_counter() - t0) * 1000

    # 10. Confidence Engine
    t0 = time.perf_counter()
    conf_score, conf_level = confidence_engine.calculate_confidence(
        reranked_evidence, ground_status, claims_passed, asr_conf
    )
    stages["10. Confidence Engine"] = (time.perf_counter() - t0) * 1000

    # 11. Translation Layer
    t0 = time.perf_counter()
    translated_answer = await translation_engine.translate(raw_answer, detected_lang)
    stages["11. Translation Layer"] = (time.perf_counter() - t0) * 1000

    # 12. TTS Audio Synthesis
    t0 = time.perf_counter()
    audio_url = await tts_engine.synthesize(query_id, translated_answer, detected_lang)
    stages["12. TTS Engine (Voice Synthesis)"] = (time.perf_counter() - t0) * 1000

    # 13. Audit Logging
    t0 = time.perf_counter()
    audit_logger.log_event(db, query_id, "PROFILE_SUCCESS", {"confidence": conf_score})
    stages["13. Audit Logger (DB Write)"] = (time.perf_counter() - t0) * 1000

    total_duration_ms = (time.perf_counter() - total_start) * 1000
    db.close()

    # Print Report
    print(f"\n{'STAGE NAME':<40} | {'LATENCY (ms)':<15} | {'PERCENTAGE':<12} | {'BOTTLENECK'}")
    print("-" * 80)
    for name, dur in stages.items():
        pct = (dur / total_duration_ms) * 100 if total_duration_ms > 0 else 0
        tag = "[FAST]"
        if dur > 1500:
            tag = "[CRITICAL BOTTLENECK]"
        elif dur > 300:
            tag = "[NOTICEABLE DELAY]"
        print(f"{name:<40} | {dur:>10.2f} ms   | {pct:>8.1f} %   | {tag}")

    print("-" * 80)
    print(f"{'TOTAL END-TO-END PIPELINE LATENCY':<40} | {total_duration_ms:>10.2f} ms   | 100.0 %")
    print("=" * 80 + "\n")

    return {
        "query": query_text,
        "total_duration_ms": total_duration_ms,
        "stages": stages
    }


async def main():
    test_queries = [
        ("How to control whitefly in cotton crop?", "Cotton", "en"),
        ("माझ्या सोयाबीनची पाने पिवळी पडत आहेत, काय उपाय करावा?", "Soybean", "mr"),
        ("धान में ब्लास्ट रोग की रोकथाम के लिए कौन सा स्प्रे करें?", "Rice", "hi")
    ]

    all_results = []
    for q, c, l in test_queries:
        res = await profile_single_query(q, c, l)
        all_results.append(res)

    print("\n" + "=" * 80)
    print("  EXECUTIVE BOTTLENECK SUMMARY")
    print("=" * 80)
    # Average across test queries
    avg_stages = {}
    for r in all_results:
        for k, v in r["stages"].items():
            avg_stages[k] = avg_stages.get(k, 0.0) + v / len(all_results)
    
    sorted_bottlenecks = sorted(avg_stages.items(), key=lambda x: x[1], reverse=True)
    for idx, (stg, dur) in enumerate(sorted_bottlenecks, 1):
        print(f"  {idx}. {stg:<35}: {dur:>8.2f} ms")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
