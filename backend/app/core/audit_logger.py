import uuid
from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.app.db.models import AuditEvent

class AuditLogger:
    def log_event(self, db: Session, query_id: str, event_type: str, payload: Dict[str, Any]):
        event_id = f"AUD-{uuid.uuid4().hex[:8]}"
        audit_rec = AuditEvent(
            id=event_id,
            query_id=query_id,
            event_type=event_type,
            payload=payload
        )
        db.add(audit_rec)
        db.commit()

audit_logger = AuditLogger()
