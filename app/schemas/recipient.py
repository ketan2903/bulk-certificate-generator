from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from app.models.recipient import RecipientStatus

class RecipientInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Full name of recipient")
    email: EmailStr = Field(..., description="Valid email address of recipient")
    issue_date: Optional[str] = Field(None, max_length=50, description="Optional date string (e.g. '2026-10-08' or 'October 8, 2026')")
    grade_or_score: Optional[str] = Field(None, max_length=50, description="Optional score/grade/honors (e.g. '98%', 'Grade A', 'With Distinction')")
    custom_message: Optional[str] = Field(None, max_length=500, description="Optional custom recognition message")

    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Recipient name cannot be blank or whitespace only")
        return v.strip()

class RecipientResponse(BaseModel):
    id: str
    name: str
    email: str
    issue_date: Optional[str] = None
    grade_or_score: Optional[str] = None
    custom_message: Optional[str] = None
    status: RecipientStatus
    error_message: Optional[str] = None
    certificate_id: Optional[str] = None
    certificate_number: Optional[str] = None
    download_url: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
