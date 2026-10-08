from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.job import GenerationJob, JobStatus
from app.models.recipient import Recipient, RecipientStatus
from app.models.certificate import Certificate
from app.schemas.job import JobCreateRequest, JobSummaryResponse, JobDetailResponse, JobListResponse
from app.schemas.recipient import RecipientResponse
from app.utils.file_utils import create_job_zip_archive
from app.config import settings

class JobService:
    @staticmethod
    def create_job(db: Session, request: JobCreateRequest) -> GenerationJob:
        """Create a new job and bulk-insert its recipients."""
        job = GenerationJob(
            event_name=request.event_name,
            organization_name=request.organization_name or settings.DEFAULT_ORGANIZATION,
            issuer_name=request.issuer_name or settings.DEFAULT_SIGNATORY_NAME,
            issuer_title=request.issuer_title or settings.DEFAULT_SIGNATORY_TITLE,
            status=JobStatus.PENDING,
            total_recipients=len(request.recipients),
            successful_recipients=0,
            failed_recipients=0,
        )
        db.add(job)
        db.flush() # populate job.id

        # Add recipients
        recipients = [
            Recipient(
                job_id=job.id,
                name=r.name,
                email=str(r.email),
                issue_date=r.issue_date,
                grade_or_score=r.grade_or_score,
                custom_message=r.custom_message,
                status=RecipientStatus.PENDING,
            )
            for r in request.recipients
        ]
        db.add_all(recipients)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def _format_recipient_response(r: Recipient) -> RecipientResponse:
        """Format recipient ORM entity into Pydantic schema with certificate links."""
        cert_id = r.certificate.id if r.certificate else None
        cert_number = r.certificate.certificate_number if r.certificate else None
        download_url = f"/api/v1/certificates/{cert_id}/download" if cert_id else None

        return RecipientResponse(
            id=r.id,
            name=r.name,
            email=r.email,
            issue_date=r.issue_date,
            grade_or_score=r.grade_or_score,
            custom_message=r.custom_message,
            status=r.status,
            error_message=r.error_message,
            certificate_id=cert_id,
            certificate_number=cert_number,
            download_url=download_url,
            created_at=r.created_at,
        )

    @staticmethod
    def _calculate_progress(job: GenerationJob) -> float:
        """Compute real-time job progress as a percentage (0.0 to 100.0)."""
        if job.total_recipients == 0:
            return 100.0
        if job.status in [JobStatus.COMPLETED, JobStatus.PARTIALLY_FAILED, JobStatus.FAILED]:
            return 100.0
        processed = job.successful_recipients + job.failed_recipients
        return round((processed / job.total_recipients) * 100.0, 1)

    @staticmethod
    def get_job_summary(job: GenerationJob) -> JobSummaryResponse:
        """Format job summary response."""
        zip_url = f"/api/v1/jobs/{job.id}/download-zip" if job.successful_recipients > 0 else None
        return JobSummaryResponse(
            id=job.id,
            event_name=job.event_name,
            organization_name=job.organization_name,
            issuer_name=job.issuer_name,
            issuer_title=job.issuer_title,
            status=job.status,
            total_recipients=job.total_recipients,
            successful_recipients=job.successful_recipients,
            failed_recipients=job.failed_recipients,
            progress_percentage=JobService._calculate_progress(job),
            created_at=job.created_at,
            updated_at=job.updated_at,
            completed_at=job.completed_at,
            download_all_zip_url=zip_url,
        )

    @staticmethod
    def get_job_detail(db: Session, job_id: str) -> JobDetailResponse:
        """Retrieve full details of a job, including all recipient statuses and certificate links."""
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job with ID '{job_id}' not found.")

        recipients_list = [JobService._format_recipient_response(r) for r in job.recipients]
        summary = JobService.get_job_summary(job)

        return JobDetailResponse(
            **summary.model_dump(),
            error_summary=job.error_summary,
            recipients=recipients_list,
        )

    @staticmethod
    def list_jobs(db: Session, skip: int = 0, limit: int = 50) -> JobListResponse:
        """List generation jobs with pagination."""
        total = db.query(GenerationJob).count()
        jobs = db.query(GenerationJob).order_by(GenerationJob.created_at.desc()).offset(skip).limit(limit).all()
        return JobListResponse(
            total=total,
            items=[JobService.get_job_summary(j) for j in jobs]
        )

    @staticmethod
    def generate_job_zip(db: Session, job_id: str) -> Tuple[str, str]:
        """
        Creates a ZIP archive of all successfully generated certificates in the job.
        Returns: (zip_file_path, suggested_filename)
        """
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job with ID '{job_id}' not found.")

        certificates = db.query(Certificate).filter(Certificate.job_id == job_id).all()
        if not certificates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No certificates have been successfully generated for job '{job_id}' yet."
            )

        files_to_zip = [(cert.file_path, cert.file_name) for cert in certificates]
        zip_path = create_job_zip_archive(job_id, files_to_zip)
        suggested_name = f"{job.event_name.replace(' ', '_')}_Certificates.zip"

        return zip_path, suggested_name
