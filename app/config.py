import os
from pathlib import Path
from pydantic import BaseModel, ConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseModel):
    PROJECT_NAME: str = "Bulk Certificate Generator"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Storage settings
    STORAGE_DIR: Path = BASE_DIR / "storage"
    CERTIFICATES_DIR: Path = STORAGE_DIR / "certificates"
    ARCHIVES_DIR: Path = STORAGE_DIR / "archives"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'certificate_generator.db'}")
    
    # Organization defaults for certificates
    DEFAULT_ORGANIZATION: str = "Global Academy of Tech & Leadership"
    DEFAULT_SIGNATORY_NAME: str = "Dr. Eleanor Vance"
    DEFAULT_SIGNATORY_TITLE: str = "Director of Certification"
    BASE_VERIFICATION_URL: str = "http://localhost:8000/api/v1/certificates/verify"
    
    model_config = ConfigDict(arbitrary_types_allowed=True)

settings = Settings()

# Ensure directories exist
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
settings.CERTIFICATES_DIR.mkdir(parents=True, exist_ok=True)
settings.ARCHIVES_DIR.mkdir(parents=True, exist_ok=True)
