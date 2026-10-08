from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.models.job import JobStatus
from app.schemas.recipient import RecipientInput, RecipientResponse

class JobCreateRequest(BaseModel):
    event_name: str = Field(..., min_length=2, max_length=255, description="Name of the course, training, or event")
    organization_name: Optional[str] = Field(None, max_length=255, description="Issuing organization (e.g. 'Acme Learning Corp')")
    issuer_name: Optional[str] = Field(None, max_length=255, description="Name of signing authority (e.g. 'Jane Doe')")
    issuer_title: Optional[str] = Field(None, max_length=255, description="Title of signing authority (e.g. 'Program Director')")
    recipients: List[RecipientInput] = Field(..., min_length=1, description="List of recipient records to generate certificates for")

    @field_validator("event_name")
    @classmethod
    def validate_event_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Event name cannot be blank or whitespace only")
        return v.strip()

class JobSummaryResponse(BaseModel):
    id: str
    event_name: str
    organization_name: Optional[str] = None
    issuer_name: Optional[str] = None
    issuer_title: Optional[str] = None
    status: JobStatus
    total_recipients: int
    successful_recipients: int
    failed_recipients: int
    progress_percentage: float
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    download_all_zip_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class JobDetailResponse(JobSummaryResponse):
    error_summary: Optional[str] = None
    recipients: List[RecipientResponse] = []

class JobListResponse(BaseModel):
    total: int
    items: List[JobSummaryResponse]
