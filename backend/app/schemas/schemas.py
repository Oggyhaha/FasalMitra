from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime

class AdvisoryQueryRequest(BaseModel):
    farmer_id: Optional[str] = "FARM-1001"
    channel: str = Field(default="WEB_SIMULATOR", description="PHONE, WHATSAPP, WEB_SIMULATOR")
    language: str = Field(default="auto", description="mr, hi, gu, en, auto")
    text: str
    audio_base64: Optional[str] = None
    crop_override: Optional[str] = None
    crop_stage_days: Optional[int] = 35
    location_district: Optional[str] = "Latur"
    location_state: Optional[str] = "Maharashtra"

class EvidenceChunk(BaseModel):
    source_id: str
    authority: str
    title: str
    score: float
    text: str

class VerifiedClaim(BaseModel):
    claim: str
    verified: bool

class StructuredQueryInfo(BaseModel):
    intent: str
    crop: Optional[str] = None
    symptoms: List[str] = []
    chemicals_mentioned: List[str] = []
    urgency: str = "MEDIUM"

class AdvisoryQueryResponse(BaseModel):
    query_id: str
    status: str # ANSWERED, CLARIFICATION_REQUIRED, ESCALATED_TO_EXPERT
    language_detected: str
    structured_query: StructuredQueryInfo
    answer_text: str
    audio_url: Optional[str] = None
    confidence_score: float
    confidence_level: str # HIGH, MEDIUM, LOW
    grounding_status: str # SUPPORTED, INSUFFICIENT, CONFLICTING, STALE
    safety_status: str # PASSED, FAILED
    retrieved_evidence: List[EvidenceChunk] = []
    claims_verified: List[VerifiedClaim] = []
    escalation_id: Optional[str] = None

class ExpertRespondRequest(BaseModel):
    expert_id: str = "EXP-01"
    action: str = Field(default="ANSWER", description="ANSWER, REQUEST_INFO")
    verified_answer: str
    notes: Optional[str] = None

class EscalationCaseSchema(BaseModel):
    id: str
    farmer_id: str
    farmer_name: Optional[str]
    phone_number: Optional[str]
    district: Optional[str]
    crop: Optional[str]
    question: str
    risk_level: str
    reason: str
    status: str
    retrieved_evidence: Optional[Any]
    expert_answer: Optional[str]
    created_at: datetime
