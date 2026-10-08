from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import Base, engine
from app.api.routes_jobs import router as jobs_router
from app.api.routes_certificates import router as certificates_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for application initialization and cleanup."""
    # Create all database tables on startup if they don't exist
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup on shutdown if needed

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Production-ready backend API for asynchronous bulk certificate generation, "
        "tracking, failure isolation, and cryptographic authenticity verification."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for cross-origin frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(jobs_router, prefix=settings.API_V1_PREFIX)
app.include_router(certificates_router, prefix=settings.API_V1_PREFIX)

@app.get("/", tags=["Health"])
def root():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "endpoints": {
            "create_job": f"{settings.API_V1_PREFIX}/jobs",
            "list_jobs": f"{settings.API_V1_PREFIX}/jobs",
            "check_status": f"{settings.API_V1_PREFIX}/jobs/{{job_id}}",
            "download_zip": f"{settings.API_V1_PREFIX}/jobs/{{job_id}}/download-zip",
            "download_certificate": f"{settings.API_V1_PREFIX}/certificates/{{certificate_id}}/download",
            "verify_certificate": f"{settings.API_V1_PREFIX}/certificates/verify/{{identifier}}",
        }
    }

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
