from typing import List, Tuple
from backend.app.schemas.schemas import EvidenceChunk

class ConfidenceEngine:
    def calculate_confidence(
        self,
        retrieval_evidence: List[EvidenceChunk],
        grounding_status: str,
        claims_passed: bool,
        asr_confidence: float
    ) -> Tuple[float, str]:
        """
        Calculates multi-factor overall confidence score.
        Returns: (confidence_score: float, level: str)
        """
        if grounding_status != "SUPPORTED" or not claims_passed:
            return 0.35, "LOW"

        top_evidence_score = retrieval_evidence[0].score if retrieval_evidence else 0.0
        
        # Weighted formula
        final_score = (top_evidence_score * 0.5) + (asr_confidence * 0.3) + (1.0 if claims_passed else 0.0) * 0.2
        final_score = round(min(0.98, max(0.1, final_score)), 2)

        if final_score >= 0.75:
            level = "HIGH"
        elif final_score >= 0.55:
            level = "MEDIUM"
        else:
            level = "LOW"

        return final_score, level

confidence_engine = ConfidenceEngine()
