import pytest
import asyncio
from backend.app.core.asr_engine import asr_engine
from backend.app.core.query_understanding import query_understanding_engine
from backend.app.core.safety_gate import pre_safety_gate
from backend.app.core.grounding_gate import grounding_gate
from backend.app.core.claim_verifier import claim_verifier
from backend.app.schemas.schemas import EvidenceChunk

@pytest.mark.asyncio
async def test_asr_engine_language_detection():
    transcript, lang, conf = await asr_engine.transcribe("माझ्या सोयाबीनची पाने पिवळी पडत आहेत")
    assert lang == "mr"
    assert "सोयाबीन" in transcript

@pytest.mark.asyncio
async def test_query_understanding_entity_extraction():
    res = query_understanding_engine.parse_query("माझ्या सोयाबीनची पाने पिवळी पडत आहेत", crop_override="Soybean")
    assert res["intent"] == "PEST_DISEASE"
    assert res["crop"] == "Soybean"
    assert "yellowing" in res["symptoms"]

@pytest.mark.asyncio
async def test_pre_safety_gate_rejection():
    # Test banned chemical / out of domain refusal
    nlp_res = query_understanding_engine.parse_query("Spraying paraquat mix")
    nlp_res["chemicals_mentioned"] = ["paraquat"]
    passed, risk, reason = pre_safety_gate.evaluate("Spraying paraquat mix", nlp_res, {"crop": "Wheat"})
    assert passed is False
    assert "HIGH_RISK_BANNED_CHEMICAL" in reason

@pytest.mark.asyncio
async def test_grounding_gate_insufficient_evidence():
    status, reason = grounding_gate.evaluate_grounding([], "PEST_DISEASE", "MEDIUM")
    assert status == "INSUFFICIENT"
    assert reason == "NO_EVIDENCE_FOUND_IN_KNOWLEDGE_BASE"

@pytest.mark.asyncio
async def test_claim_verifier_validation():
    evidence = [EvidenceChunk(
        source_id="S1", authority="KVK", title="T1", score=0.9,
        text="Spray Thiamethoxam 25% WG at 100g per hectare."
    )]
    claims, passed = claim_verifier.verify_claims("Spray 100g per hectare of Thiamethoxam", evidence)
    assert passed is True

@pytest.mark.asyncio
async def test_grounding_gate_supported():
    evidence = [EvidenceChunk(
        source_id="S1", authority="KVK Latur Advisory", title="Soybean Yellow Mosaic", score=0.85,
        text="Spray Thiamethoxam 25% WG at 100g per hectare."
    )]
    status, reason = grounding_gate.evaluate_grounding(evidence, "PEST_DISEASE", "LOW")
    assert status == "SUPPORTED"
