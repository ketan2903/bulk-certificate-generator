import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class RecipientStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class Recipient(Base):
    __tablename__ = "recipients"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    job_id = Column(String(36), ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    issue_date = Column(String(50), nullable=True)
    grade_or_score = Column(String(50), nullable=True)
    custom_message = Column(Text, nullable=True)
    
    status = Column(Enum(RecipientStatus), default=RecipientStatus.PENDING, nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    # Relationships
    job = relationship("GenerationJob", back_populates="recipients")
    certificate = relationship("Certificate", back_populates="recipient", uselist=False, cascade="all, delete-orphan")
