import io
import csv
from typing import Optional
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.job import JobCreateRequest, JobSummaryResponse, JobDetailResponse, JobListResponse
from app.schemas.recipient import RecipientInput
from app.services.job_service import JobService
from app.services.background_worker import process_bulk_certificate_job

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.post(
    "",
    response_model=JobSummaryResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a bulk certificate generation job",
    description="Accepts event details and a list of recipients. Enqueues generation in the background and returns job status."
)
def create_bulk_certificate_job(
    request: JobCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Submit a bulk certificate generation job.
    Processing is offloaded to a background task so the API responds instantly.
    """
    if not request.recipients:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one recipient must be provided in the recipients list."
        )

    # Create job record in DB
    job = JobService.create_job(db, request)

    # Launch background worker
    background_tasks.add_task(process_bulk_certificate_job, job.id)

    return JobService.get_job_summary(job)

@router.post(
    "/upload-csv",
    response_model=JobSummaryResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit bulk certificate generation via CSV file upload",
    description="Accepts a CSV file with columns (name, email, issue_date, grade_or_score, custom_message) along with event metadata."
)
async def create_job_from_csv(
    background_tasks: BackgroundTasks,
    event_name: str = Form(..., description="Name of the course/event"),
    organization_name: Optional[str] = Form(None, description="Issuing organization"),
    issuer_name: Optional[str] = Form(None, description="Issuer / Signatory name"),
    issuer_title: Optional[str] = Form(None, description="Issuer title"),
    file: UploadFile = File(..., description="CSV file containing recipient rows"),
    db: Session = Depends(get_db)
):
    """Convenience endpoint to create a job from an uploaded CSV file."""
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only .csv files are supported."
        )

    content = await file.read()
    try:
        csv_text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not decode CSV file. Please ensure it is UTF-8 encoded."
        )

    reader = csv.DictReader(io.StringIO(csv_text))
    recipients = []
    
    for row_idx, row in enumerate(reader, start=2):
        # Normalize column keys
        clean_row = {k.strip().lower(): v.strip() for k, v in row.items() if k}
        name = clean_row.get("name") or clean_row.get("recipient_name")
        email = clean_row.get("email") or clean_row.get("recipient_email")
        
        if not name or not email:
            raise HTTPException(
                status_code=422,
                detail=f"Row {row_idx}: Both 'name' and 'email' columns are required and cannot be empty."
            )

        try:
            recipients.append(
                RecipientInput(
                    name=name,
                    email=email,
                    issue_date=clean_row.get("issue_date") or clean_row.get("date"),
                    grade_or_score=clean_row.get("grade_or_score") or clean_row.get("grade") or clean_row.get("score"),
                    custom_message=clean_row.get("custom_message") or clean_row.get("message"),
                )
            )
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Row {row_idx} validation error: {str(e)}"
            )

    if not recipients:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file contains no valid recipient data rows."
        )

    job_request = JobCreateRequest(
        event_name=event_name,
        organization_name=organization_name,
        issuer_name=issuer_name,
        issuer_title=issuer_title,
        recipients=recipients
    )

    job = JobService.create_job(db, job_request)
    background_tasks.add_task(process_bulk_certificate_job, job.id)
    return JobService.get_job_summary(job)

@router.get(
    "",
    response_model=JobListResponse,
    summary="List certificate generation jobs",
    description="Retrieve a paginated list of all certificate generation jobs."
)
def list_jobs(
    skip: int = Query(0, ge=0, description="Offset"),
    limit: int = Query(50, ge=1, le=100, description="Limit"),
    db: Session = Depends(get_db)
):
    return JobService.list_jobs(db, skip=skip, limit=limit)

@router.get(
    "/{job_id}",
    response_model=JobDetailResponse,
    summary="Get job status and progress",
    description="Check real-time progress, completion status, and per-recipient certificate links or failure reasons."
)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    return JobService.get_job_detail(db, job_id)

@router.get(
    "/{job_id}/download-zip",
    summary="Download all generated certificates as a ZIP archive",
    description="Packages all successfully generated PDF certificates for the job into a single downloadable ZIP file."
)
def download_job_certificates_zip(job_id: str, db: Session = Depends(get_db)):
    zip_path, filename = JobService.generate_job_zip(db, job_id)
    return FileResponse(
        path=zip_path,
        filename=filename,
        media_type="application/zip"
    )
