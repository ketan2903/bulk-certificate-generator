from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class CertificateResponse(BaseModel):
    id: str
    recipient_id: str
    job_id: str
    certificate_number: str
    verification_code: str
    file_name: str
    file_size_bytes: int
    download_url: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CertificateVerificationResponse(BaseModel):
    valid: bool
    certificate_number: Optional[str] = None
    recipient_name: Optional[str] = None
    recipient_email: Optional[str] = None
    event_name: Optional[str] = None
    organization_name: Optional[str] = None
    issuer_name: Optional[str] = None
    issuer_title: Optional[str] = None
    issue_date: Optional[str] = None
    grade_or_score: Optional[str] = None
    verification_code: Optional[str] = None
    sha256_hash: Optional[str] = None
    issued_at: Optional[datetime] = None
    verification_message: str
