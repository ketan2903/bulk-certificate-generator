import logging
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.job import GenerationJob, JobStatus
from app.models.recipient import Recipient, RecipientStatus
from app.models.certificate import Certificate
from app.services.certificate_generator import certificate_generator
from app.utils.file_utils import generate_verification_code

logger = logging.getLogger("bulk_certificate_generator")

def process_bulk_certificate_job(job_id: str):
    """
    Background worker task that iterates through all recipients of a job,
    generates PDF certificates with isolated error handling per recipient,
    and updates job progress and final statuses in the database.
    """
    db: Session = SessionLocal()
    try:
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found for background processing.")
            return

        # Mark job as PROCESSING
        job.status = JobStatus.PROCESSING
        db.commit()

        # Fetch recipients
        recipients = db.query(Recipient).filter(Recipient.job_id == job_id).all()
        
        success_count = 0
        failure_count = 0
        errors = []

        for recipient in recipients:
            try:
                # Artificial error trigger test hook for resilient testing if requested
                if recipient.name.startswith("__FAIL__"):
                    raise ValueError(f"Simulated generation failure for recipient {recipient.name}")

                # Unique certificate number: CERT-YYYYMMDD-<short_uuid>
                now = datetime.now(timezone.utc)
                date_prefix = now.strftime("%Y%m%d")
                short_id = uuid.uuid4().hex[:8].upper()
                cert_number = f"CERT-{date_prefix}-{short_id}"
                verification_code = generate_verification_code()

                # Generate certificate PDF
                pdf_meta = certificate_generator.generate_certificate(
                    recipient_name=recipient.name,
                    recipient_email=recipient.email,
                    event_name=job.event_name,
                    certificate_number=cert_number,
                    verification_code=verification_code,
                    organization_name=job.organization_name,
                    issuer_name=job.issuer_name,
                    issuer_title=job.issuer_title,
                    issue_date=recipient.issue_date,
                    grade_or_score=recipient.grade_or_score,
                    custom_message=recipient.custom_message,
                )

                # Create Certificate database record
                certificate = Certificate(
                    recipient_id=recipient.id,
                    job_id=job.id,
                    certificate_number=cert_number,
                    verification_code=verification_code,
                    sha256_hash=pdf_meta["sha256_hash"],
                    file_name=pdf_meta["file_name"],
                    file_path=pdf_meta["file_path"],
                    file_size_bytes=pdf_meta["file_size_bytes"],
                )
                db.add(certificate)

                # Update recipient status
                recipient.status = RecipientStatus.SUCCESS
                recipient.error_message = None
                success_count += 1

            except Exception as ex:
                logger.exception(f"Failed to generate certificate for recipient {recipient.id} ({recipient.name}): {ex}")
                recipient.status = RecipientStatus.FAILED
                recipient.error_message = str(ex)
                failure_count += 1
                errors.append(f"{recipient.name} ({recipient.email}): {str(ex)}")

            # Update real-time job counters
            job.successful_recipients = success_count
            job.failed_recipients = failure_count
            db.commit()

        # Update final job status
        job.completed_at = datetime.now(timezone.utc)
        if failure_count == 0:
            job.status = JobStatus.COMPLETED
        elif success_count > 0 and failure_count > 0:
            job.status = JobStatus.PARTIALLY_FAILED
            job.error_summary = f"{failure_count} recipient(s) failed. Errors: " + "; ".join(errors[:5])
        else:
            job.status = JobStatus.FAILED
            job.error_summary = f"All {failure_count} recipient(s) failed. Errors: " + "; ".join(errors[:5])

        db.commit()
        logger.info(f"Job {job_id} finished processing. Success: {success_count}, Failed: {failure_count}, Status: {job.status}")

    except Exception as e:
        logger.critical(f"Critical error during job processing {job_id}: {e}", exc_info=True)
        try:
            job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
            if job:
                job.status = JobStatus.FAILED
                job.error_summary = f"Unexpected system error: {str(e)}"
                job.completed_at = datetime.now(timezone.utc)
                db.commit()
        except Exception:
            pass
    finally:
        db.close()
