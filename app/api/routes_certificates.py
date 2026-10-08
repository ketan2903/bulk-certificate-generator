import os
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.certificate import Certificate
from app.models.recipient import Recipient
from app.models.job import GenerationJob
from app.schemas.certificate import CertificateResponse, CertificateVerificationResponse

router = APIRouter(prefix="/certificates", tags=["Certificates"])

@router.get(
    "/{certificate_id}",
    response_model=CertificateResponse,
    summary="Get certificate metadata",
    description="Retrieve metadata for a specific generated certificate."
)
def get_certificate_metadata(certificate_id: str, db: Session = Depends(get_db)):
    cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate with ID '{certificate_id}' not found."
        )

    return CertificateResponse(
        id=cert.id,
        recipient_id=cert.recipient_id,
        job_id=cert.job_id,
        certificate_number=cert.certificate_number,
        verification_code=cert.verification_code,
        file_name=cert.file_name,
        file_size_bytes=cert.file_size_bytes,
        download_url=f"/api/v1/certificates/{cert.id}/download",
        created_at=cert.created_at,
    )

@router.get(
    "/{certificate_id}/download",
    summary="Download certificate PDF",
    description="Download or stream the generated PDF certificate."
)
def download_certificate(
    certificate_id: str,
    inline: bool = Query(False, description="Set True to view in browser instead of attachment download"),
    db: Session = Depends(get_db)
):
    cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate with ID '{certificate_id}' not found."
        )

    if not os.path.exists(cert.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate PDF file is missing from storage."
        )

    content_disposition = "inline" if inline else f'attachment; filename="{cert.file_name}"'

    return FileResponse(
        path=cert.file_path,
        filename=cert.file_name,
        media_type="application/pdf",
        headers={"Content-Disposition": content_disposition}
    )

@router.get(
    "/verify/{identifier}",
    response_model=CertificateVerificationResponse,
    summary="Verify certificate authenticity",
    description="Public verification endpoint. Verify a certificate by either its certificate number or its verification token."
)
def verify_certificate(identifier: str, db: Session = Depends(get_db)):
    """
    Public lookup to verify the authenticity of a certificate.
    Matches against either certificate_number or verification_code.
    """
    cert = (
        db.query(Certificate)
        .filter(
            (Certificate.certificate_number == identifier) |
            (Certificate.verification_code == identifier)
        )
        .first()
    )

    if not cert:
        return CertificateVerificationResponse(
            valid=False,
            verification_message=f"No active certificate found matching '{identifier}'."
        )

    recipient = db.query(Recipient).filter(Recipient.id == cert.recipient_id).first()
    job = db.query(GenerationJob).filter(GenerationJob.id == cert.job_id).first()

    return CertificateVerificationResponse(
        valid=True,
        certificate_number=cert.certificate_number,
        recipient_name=recipient.name if recipient else None,
        recipient_email=recipient.email if recipient else None,
        event_name=job.event_name if job else None,
        organization_name=job.organization_name if job else None,
        issuer_name=job.issuer_name if job else None,
        issuer_title=job.issuer_title if job else None,
        issue_date=recipient.issue_date if recipient else None,
        grade_or_score=recipient.grade_or_score if recipient else None,
        verification_code=cert.verification_code,
        sha256_hash=cert.sha256_hash,
        issued_at=cert.created_at,
        verification_message="Certificate is authentic, verified, and issued by an authorized organization."
    )
