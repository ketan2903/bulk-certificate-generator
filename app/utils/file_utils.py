import os
import re
import zipfile
import hashlib
import secrets
from pathlib import Path
from typing import List, Tuple
from app.config import settings

def sanitize_filename(name: str) -> str:
    """Sanitize a string to be safely used as a filename."""
    # Keep alphanumeric, spaces, dashes, and underscores
    clean = re.sub(r'[^a-zA-Z0-9_\-\s]', '', name)
    clean = re.sub(r'\s+', '_', clean.strip())
    return clean or "certificate"

def generate_verification_code() -> str:
    """Generate a secure cryptographic 16-character hex verification token."""
    return secrets.token_hex(8).upper()

def calculate_sha256(filepath: str | Path) -> str:
    """Calculate the SHA256 checksum of a file on disk."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()

def create_job_zip_archive(job_id: str, files_to_zip: List[Tuple[str, str]]) -> str:
    """
    Creates a ZIP archive containing all generated certificate PDFs for a given job.
    files_to_zip is a list of tuples: (absolute_file_path, archive_arcname)
    Returns the absolute path to the generated zip file.
    """
    settings.ARCHIVES_DIR.mkdir(parents=True, exist_ok=True)
    zip_filename = f"job_{job_id}_certificates.zip"
    zip_path = settings.ARCHIVES_DIR / zip_filename
    
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_path, arcname in files_to_zip:
            if os.path.exists(file_path):
                zip_file.write(file_path, arcname=arcname)
                
    return str(zip_path)
