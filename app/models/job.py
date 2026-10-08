import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    PARTIALLY_FAILED = "PARTIALLY_FAILED"
    FAILED = "FAILED"

class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    event_name = Column(String(255), nullable=False)
    organization_name = Column(String(255), nullable=True)
    issuer_name = Column(String(255), nullable=True)
    issuer_title = Column(String(255), nullable=True)
    template_name = Column(String(100), default="standard_elegant")
    
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True)
    total_recipients = Column(Integer, default=0, nullable=False)
    successful_recipients = Column(Integer, default=0, nullable=False)
    failed_recipients = Column(Integer, default=0, nullable=False)
    
    error_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    recipients = relationship("Recipient", back_populates="job", cascade="all, delete-orphan", order_by="Recipient.created_at")
    certificates = relationship("Certificate", back_populates="job", cascade="all, delete-orphan")
