from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.db.database import get_db
from backend.app.db.models import Escalation
from backend.app.schemas.schemas import EscalationCaseSchema, ExpertRespondRequest

router = APIRouter(prefix="/expert", tags=["expert"])

@router.get("/escalations", response_model=List[EscalationCaseSchema])
def list_escalations(
    status: Optional[str] = "OPEN",
    risk_level: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Escalation)
    if status and status != "ALL":
        query = query.filter(Escalation.status == status)
    if risk_level:
        query = query.filter(Escalation.risk_level == risk_level)
    
    return query.order_by(Escalation.created_at.desc()).all()

@router.post("/escalations/{case_id}/respond")
def respond_to_escalation(
    case_id: str,
    req: ExpertRespondRequest,
    db: Session = Depends(get_db)
):
    case = db.query(Escalation).filter(Escalation.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Escalation case not found")

    case.status = "RESOLVED"
    case.expert_answer = req.verified_answer
    db.commit()

    return {
        "status": "SUCCESS",
        "case_id": case_id,
        "action": req.action,
        "message": "Verified expert answer recorded and sent to farmer."
    }
