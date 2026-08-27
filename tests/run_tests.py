import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
import asyncio
from backend.app.core.asr_engine import asr_engine
from backend.app.core.query_understanding import query_understanding_engine
from backend.app.core.safety_gate import pre_safety_gate
from backend.app.core.grounding_gate import grounding_gate
from backend.app.core.claim_verifier import claim_verifier
from backend.app.schemas.schemas import EvidenceChunk

class TestFasalMitraPipeline(unittest.TestCase):
    def test_asr_engine_language_detection(self):
        transcript, lang, conf = asyncio.run(asr_engine.transcribe("माझ्या सोयाबीनची पाने पिवळी पडत आहेत"))
        self.assertEqual(lang, "mr")
        self.assertIn("सोयाबीन", transcript)

    def test_query_understanding_entity_extraction(self):
        res = query_understanding_engine.parse_query("माझ्या सोयाबीनची पाने पिवळी पडत आहेत", crop_override="Soybean")
        self.assertEqual(res["intent"], "PEST_DISEASE")
        self.assertEqual(res["crop"], "Soybean")
        self.assertIn("yellowing", res["symptoms"])

    def test_pre_safety_gate_rejection(self):
        nlp_res = query_understanding_engine.parse_query("Spraying paraquat mix")
        nlp_res["chemicals_mentioned"] = ["paraquat"]
        passed, risk, reason = pre_safety_gate.evaluate("Spraying paraquat mix", nlp_res, {"crop": "Wheat"})
        self.assertFalse(passed)
        self.assertIn("HIGH_RISK_BANNED_CHEMICAL", reason)

    def test_grounding_gate_insufficient_evidence(self):
        status, reason = grounding_gate.evaluate_grounding([], "PEST_DISEASE", "MEDIUM")
        self.assertEqual(status, "INSUFFICIENT")
        self.assertEqual(reason, "NO_EVIDENCE_FOUND_IN_KNOWLEDGE_BASE")

    def test_grounding_gate_supported(self):
        evidence = [EvidenceChunk(
            source_id="S1", authority="KVK Latur Advisory", title="Soybean Yellow Mosaic", score=0.85,
            text="Spray Thiamethoxam 25% WG at 100g per hectare."
        )]
        status, reason = grounding_gate.evaluate_grounding(evidence, "PEST_DISEASE", "LOW")
        self.assertEqual(status, "SUPPORTED")

    def test_claim_verifier_validation(self):
        evidence = [EvidenceChunk(
            source_id="S1", authority="KVK", title="T1", score=0.9,
            text="Spray Thiamethoxam 25% WG at 100g per hectare."
        )]
        claims, passed = claim_verifier.verify_claims("Spray 100g per hectare of Thiamethoxam", evidence)
        self.assertTrue(passed)

if __name__ == '__main__':
    unittest.main()
