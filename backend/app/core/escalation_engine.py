import uuid
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.app.db.models import Escalation
from backend.app.schemas.schemas import EvidenceChunk

class EscalationEngine:
    def create_escalation(
        self,
        db: Session,
        farmer_id: str,
        message_id: str,
        question: str,
        crop: str,
        district: str,
        risk_level: str,
        reason: str,
        evidence: List[EvidenceChunk]
    ) -> str:
        escalation_id = f"ESC-{uuid.uuid4().hex[:8].upper()}"
        
        evidence_json = [
            {"source_id": e.source_id, "title": e.title, "authority": e.authority, "score": e.score, "text": e.text}
            for e in evidence
        ]

        escalation_record = Escalation(
            id=escalation_id,
            message_id=message_id,
            farmer_id=farmer_id,
            farmer_name="Ramesh Patil",
            phone_number="+91 98230 12345",
            district=district,
            crop=crop,
            question=question,
            risk_level=risk_level,
            reason=reason,
            status="OPEN",
            retrieved_evidence=evidence_json
        )

        db.add(escalation_record)
        db.commit()
        return escalation_id

escalation_engine = EscalationEngine()
