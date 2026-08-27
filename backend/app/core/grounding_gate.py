from typing import List, Tuple
from backend.app.schemas.schemas import EvidenceChunk

class GroundingGate:
    def evaluate_grounding(
        self,
        evidence: List[EvidenceChunk],
        query_intent: str,
        risk_level: str
    ) -> Tuple[str, str]:
        """
        Returns: (status: str, reason: str)
        Status: SUPPORTED | INSUFFICIENT | CONFLICTING | STALE
        """
        if not evidence:
            return "INSUFFICIENT", "NO_EVIDENCE_FOUND_IN_KNOWLEDGE_BASE"

        top_score = evidence[0].score

        # High risk requires high evidence confidence score threshold
        if risk_level == "HIGH" and top_score < 0.65:
            return "INSUFFICIENT", f"HIGH_RISK_QUERY_TOP_SCORE_{top_score}_BELOW_THRESHOLD_0.65"

        if top_score < 0.40:
            return "INSUFFICIENT", f"TOP_SCORE_{top_score}_BELOW_MINIMUM_THRESHOLD_0.40"

        return "SUPPORTED", "EVIDENCE_SUFFICIENT_FOR_GROUNDED_GENERATION"

grounding_gate = GroundingGate()
