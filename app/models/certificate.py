import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    recipient_id = Column(String(36), ForeignKey("recipients.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    job_id = Column(String(36), ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    certificate_number = Column(String(100), unique=True, nullable=False, index=True)
    verification_code = Column(String(64), unique=True, nullable=False, index=True)
    sha256_hash = Column(String(64), nullable=True)
    
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, nullable=False, default=0)
    
    created_at = Column(DateTime, default=utc_now, nullable=False)

    # Relationships
    recipient = relationship("Recipient", back_populates="certificate")
    job = relationship("GenerationJob", back_populates="certificates")
