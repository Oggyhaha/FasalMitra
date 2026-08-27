from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.db.database import Base

class Farmer(Base):
    __tablename__ = "farmers"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone_number = Column(String, unique=True, index=True)
    preferred_language = Column(String, default="hi")
    state = Column(String, nullable=True)
    district = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    farms = relationship("Farm", back_populates="farmer", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="farmer", cascade="all, delete-orphan")


class Farm(Base):
    __tablename__ = "farms"

    id = Column(String, primary_key=True, index=True)
    farmer_id = Column(String, ForeignKey("farmers.id"), nullable=False)
    farm_name = Column(String, default="Main Farm")
    area_acres = Column(Float, default=2.5)
    soil_type = Column(String, nullable=True)
    district = Column(String, nullable=False)
    state = Column(String, nullable=False)

    farmer = relationship("Farmer", back_populates="farms")
    crop_passports = relationship("CropPassport", back_populates="farm", cascade="all, delete-orphan")


class CropPassport(Base):
    __tablename__ = "crop_passports"

    id = Column(String, primary_key=True, index=True)
    farm_id = Column(String, ForeignKey("farms.id"), nullable=False)
    crop_name = Column(String, nullable=False, index=True)
    variety = Column(String, nullable=True)
    sowing_date = Column(String, nullable=True)
    stage_days = Column(Integer, default=30)
    season = Column(String, default="Kharif")

    farm = relationship("Farm", back_populates="crop_passports")


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(String, primary_key=True, index=True)
    source_name = Column(String, nullable=False) # ICAR, KVK, KCC, IMD
    authority_tier = Column(Integer, default=1)
    title = Column(String, nullable=False)
    crop = Column(String, index=True)
    stage_min_days = Column(Integer, default=0)
    stage_max_days = Column(Integer, default=120)
    district = Column(String, index=True)
    state = Column(String, index=True)
    content = Column(Text, nullable=False)
    valid_from = Column(String, nullable=True)
    valid_until = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, index=True)
    farmer_id = Column(String, ForeignKey("farmers.id"), nullable=False)
    channel = Column(String, default="PHONE") # PHONE, WHATSAPP, WEB
    status = Column(String, default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow)

    farmer = relationship("Farmer", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    sender = Column(String, nullable=False) # FARMER, SYSTEM, EXPERT
    raw_text = Column(Text, nullable=False)
    language = Column(String, default="hi")
    audio_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


class Escalation(Base):
    __tablename__ = "escalations"

    id = Column(String, primary_key=True, index=True)
    message_id = Column(String, nullable=False)
    farmer_id = Column(String, nullable=False)
    farmer_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    district = Column(String, nullable=True)
    crop = Column(String, nullable=True)
    question = Column(Text, nullable=False)
    risk_level = Column(String, default="MEDIUM") # HIGH, MEDIUM, LOW
    reason = Column(String, nullable=False) # GROUNDING_FAILED, HIGH_RISK_CHEMICAL, LOW_CONFIDENCE
    status = Column(String, default="OPEN") # OPEN, RESOLVED
    retrieved_evidence = Column(JSON, nullable=True)
    expert_answer = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String, primary_key=True, index=True)
    query_id = Column(String, index=True, nullable=False)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
