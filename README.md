# Bulk Certificate Generator Backend API

A high-performance, resilient backend API built with **FastAPI**, **SQLAlchemy**, and **ReportLab** to generate personalized certificates in bulk for event attendees, students, and employees.

---

## Table of Contents
1. [Overview & Architecture](#overview--architecture)
2. [Key Features](#key-features)
3. [Design & Technical Decisions](#design--technical-decisions)
4. [Project Structure](#project-structure)
5. [Prerequisites & Installation](#prerequisites--installation)
6. [Running the Application](#running-the-application)
7. [Running the Test Suite](#running-the-test-suite)
8. [API Reference & Usage Examples](#api-reference--usage-examples)
   - [1. Submit Bulk Generation Job (JSON)](#1-submit-bulk-generation-job-json)
   - [2. Submit Bulk Generation Job (CSV Upload)](#2-submit-bulk-generation-job-csv-upload)
   - [3. Check Job Status & Progress](#3-check-job-status--progress)
   - [4. Download All Certificates as ZIP](#4-download-all-certificates-as-zip)
   - [5. Download Individual Certificate PDF](#5-download-individual-certificate-pdf)
   - [6. Verify Certificate Authenticity](#6-verify-certificate-authenticity)
   - [7. List All Jobs](#7-list-all-jobs)
9. [Sample Certificate Preview](#sample-certificate-preview)
10. [Interview Q&A / Architecture Justifications](#interview-qa--architecture-justifications)

---

## Overview & Architecture

When events or training bootcamps conclude, organizations often need to issue hundreds or thousands of personalized certificates. Generating these synchronously within a single HTTP request can cause timeouts, memory spikes, and poor user experience.

This system solves this challenge with an asynchronous, decoupled architecture:
1. **Immediate Job Acceptance**: The client submits a bulk generation request containing event metadata and recipient lists. The API validates the payload and responds immediately (`HTTP 202 Accepted`) with a unique `job_id`.
2. **Background Processing & Error Isolation**: The generation task is executed in the background. Each recipient certificate is generated in isolation: if a single recipient fails (e.g. malformed data), other recipients continue uninterrupted.
3. **Progress & Status Tracking**: Clients can poll the job endpoint at any time to monitor real-time completion percentage (`0% - 100%`), success/failure counts, and recipient-level logs.
4. **Flexible Retrieval & Verification**: Clients can download individual certificates or bundle all certificates into a single `.zip` file. Certificates include embedded QR verification codes and SHA-256 checksums verifiable via a public endpoint.

---

## Key Features

- ⚡ **Asynchronous Bulk Processing**: Non-blocking architecture using FastAPI `BackgroundTasks`.
- 🛡️ **Fault-Tolerant Error Isolation**: A failure in generating one recipient's certificate never aborts the rest of the batch.
- 📊 **Granular Job Tracking**: Status states (`PENDING`, `PROCESSING`, `COMPLETED`, `PARTIALLY_FAILED`, `FAILED`) with progress counters and percentage calculation.
- 🎨 **Vector PDF Rendering**: ReportLab-based template with dual-tone navy & gold borders, official rosette badge, typography adjustments, and scannable verification QR codes.
- 🔒 **Cryptographic Integrity & Verification**: Every certificate receives a unique certificate number, secure verification token, and SHA-256 hash.
- 📦 **One-Click Batch ZIP Download**: Generates compressed ZIP archives on-demand.
- 📄 **CSV Upload Support**: Allows bulk certificate requests via standard CSV files.
- 🧪 **100% Comprehensive Test Suite**: 18 automated tests with `pytest` covering validation, generation, status flow, error isolation, retrieval, and verification.

---

## Design & Technical Decisions

### 1. Framework: FastAPI
- **Why**: Asynchronous I/O support, automatic interactive OpenAPI (`/docs`) and ReDoc (`/redoc`) documentation, native Pydantic v2 data validation, and built-in `BackgroundTasks` support.

### 2. Relational Database & ORM: SQLite + SQLAlchemy 2.0
- **Why**: Clean separation of concerns with SQLAlchemy 2.0 ORM models (`GenerationJob`, `Recipient`, `Certificate`).
- SQLite is configured as default for zero-configuration setup, while SQLAlchemy enables immediate switching to **PostgreSQL** or **MySQL** simply by changing the `DATABASE_URL` environment variable.

### 3. Certificate Generation Engine: ReportLab & Pillow
- **Why**: Vector PDF generation ensures crisp printing at any resolution without pixelation.
- Direct programmatic canvas rendering allows sub-millimeter precision for borders, typography, rosette seals, and dynamically generated QR codes.

### 4. Background Processing Architecture
- For standard workloads, FastAPI `BackgroundTasks` provides zero-external-dependency background processing.
- The worker service (`app/services/background_worker.py`) is decoupled from the web routes, meaning it can be plugged into a distributed task queue (**Celery + Redis** or **ARQ / RQ**) if horizontal scaling across worker nodes is required.

---

## Project Structure

```
Bulk/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI application setup, lifecycle, CORS
│   ├── config.py                   # Central settings & directories
│   ├── database.py                 # SQLAlchemy engine & session factory
│   ├── models/                     # Database ORM models
│   │   ├── __init__.py
│   │   ├── job.py                  # GenerationJob model & JobStatus enum
│   │   ├── recipient.py            # Recipient model & RecipientStatus enum
│   │   └── certificate.py          # Certificate model (file paths, hashes, numbers)
│   ├── schemas/                    # Pydantic v2 validation schemas
│   │   ├── __init__.py
│   │   ├── job.py                  # Request/response schemas for jobs
│   │   ├── recipient.py            # Recipient input and output schemas
│   │   └── certificate.py          # Certificate response & verification schema
│   ├── services/                   # Core business logic
│   │   ├── __init__.py
│   │   ├── certificate_generator.py # ReportLab PDF canvas & QR code generator
│   │   ├── job_service.py          # Job creation, listing, status formatting, ZIP bundling
│   │   └── background_worker.py    # Isolated background processing worker
│   ├── api/                        # REST API Routers
│   │   ├── __init__.py
│   │   ├── routes_jobs.py          # /api/v1/jobs endpoints
│   │   └── routes_certificates.py  # /api/v1/certificates endpoints
│   └── utils/                      # Helper utilities
│       ├── __init__.py
│       └── file_utils.py           # Filename sanitization, SHA-256, ZIP packing
├── sample_data/
│   ├── sample_recipients.json      # Sample JSON payload
│   └── sample_recipients.csv       # Sample CSV upload file
├── scripts/
│   └── demo_run.py                 # Standalone script demonstrating full workflow
├── tests/                          # Automated pytest suite
│   ├── __init__.py
│   ├── conftest.py                 # Pytest fixtures and isolated test DB
│   ├── test_job_creation.py        # Job creation & listing tests
│   ├── test_validation.py          # Input validation tests
│   ├── test_certificate_generator.py # Direct PDF generation unit tests
│   ├── test_job_status.py          # Job status and progress tracking tests
│   ├── test_failure_handling.py    # Error isolation and failure tests
│   ├── test_retrieval.py           # PDF and ZIP download tests
│   └── test_verification.py        # Certificate authenticity verification tests
├── requirements.txt
└── README.md
```

---

## Prerequisites & Installation

### 1. Requirements
- Python 3.10+ (tested on Python 3.12)
- `pip` package manager

### 2. Clone / Setup
```bash
# Navigate to the project directory
cd Bulk

# Create a virtual environment (optional but recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Running the Application

Start the FastAPI server using `uvicorn`:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Once running, access:
- **Interactive Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **API Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## Running the Test Suite

Execute the complete pytest suite:

```bash
python -m pytest tests/ -v
```

All 18 tests cover:
- Job creation and persistence
- Input validation (empty names, invalid emails, empty lists, malformed CSVs)
- Direct PDF vector generation and magic header check (`%PDF-`)
- Real-time job status tracking and percentage computation
- Per-recipient failure isolation (`PARTIALLY_FAILED` state)
- Individual PDF streaming/downloading and 404 responses
- Bulk ZIP packaging and archive integrity
- Public cryptographic verification endpoint

---

## API Reference & Usage Examples

### 1. Submit Bulk Generation Job (JSON)
- **Endpoint**: `POST /api/v1/jobs`
- **Status**: `202 Accepted`

#### Example Request (`curl`):
```bash
curl -X POST "http://localhost:8000/api/v1/jobs" \
     -H "Content-Type: application/json" \
     -d '{
       "event_name": "Executive Masterclass in Generative AI",
       "organization_name": "DeepMind Academy",
       "issuer_name": "Dr. Alan Turing",
       "issuer_title": "Director of Research",
       "recipients": [
         {
           "name": "Sarah Connor",
           "email": "sarah.connor@example.com",
           "issue_date": "October 8, 2026",
           "grade_or_score": "High Distinction (98%)",
           "custom_message": "Excellence in AI system design."
         },
         {
           "name": "Bruce Wayne",
           "email": "bruce.wayne@waynecorp.com",
           "issue_date": "October 8, 2026",
           "grade_or_score": "Distinction (92%)"
         }
       ]
     }'
```

#### Example Response:
```json
{
  "id": "72d527ec-761b-4b91-9670-8cdbdac9cdae",
  "event_name": "Executive Masterclass in Generative AI",
  "organization_name": "DeepMind Academy",
  "issuer_name": "Dr. Alan Turing",
  "issuer_title": "Director of Research",
  "status": "PENDING",
  "total_recipients": 2,
  "successful_recipients": 0,
  "failed_recipients": 0,
  "progress_percentage": 0.0,
  "created_at": "2026-10-08T05:38:11Z",
  "updated_at": "2026-10-08T05:38:11Z",
  "completed_at": null,
  "download_all_zip_url": null
}
```

---

### 2. Submit Bulk Generation Job (CSV Upload)
- **Endpoint**: `POST /api/v1/jobs/upload-csv`
- **Status**: `202 Accepted`

```bash
curl -X POST "http://localhost:8000/api/v1/jobs/upload-csv" \
     -F "event_name=Cloud Architecture Bootcamp" \
     -F "organization_name=Tech Institute" \
     -F "file=@sample_data/sample_recipients.csv"
```

---

### 3. Check Job Status & Progress
- **Endpoint**: `GET /api/v1/jobs/{job_id}`
- **Status**: `200 OK`

```bash
curl -X GET "http://localhost:8000/api/v1/jobs/72d527ec-761b-4b91-9670-8cdbdac9cdae"
```

#### Example Response:
```json
{
  "id": "72d527ec-761b-4b91-9670-8cdbdac9cdae",
  "event_name": "Executive Masterclass in Generative AI",
  "organization_name": "DeepMind Academy",
  "issuer_name": "Dr. Alan Turing",
  "issuer_title": "Director of Research",
  "status": "COMPLETED",
  "total_recipients": 2,
  "successful_recipients": 2,
  "failed_recipients": 0,
  "progress_percentage": 100.0,
  "created_at": "2026-10-08T05:38:11Z",
  "updated_at": "2026-10-08T05:38:12Z",
  "completed_at": "2026-10-08T05:38:12Z",
  "download_all_zip_url": "/api/v1/jobs/72d527ec-761b-4b91-9670-8cdbdac9cdae/download-zip",
  "error_summary": null,
  "recipients": [
    {
      "id": "e0fa7bd6-14ab-46e3-8263-d34e9e4ca3b2",
      "name": "Sarah Connor",
      "email": "sarah.connor@example.com",
      "issue_date": "October 8, 2026",
      "grade_or_score": "High Distinction (98%)",
      "custom_message": "Excellence in AI system design.",
      "status": "SUCCESS",
      "error_message": null,
      "certificate_id": "30555a3b-6c68-41af-98a4-f01dd41fb070",
      "certificate_number": "CERT-20261008-4FB42ECF",
      "download_url": "/api/v1/certificates/30555a3b-6c68-41af-98a4-f01dd41fb070/download",
      "created_at": "2026-10-08T05:38:11Z"
    }
  ]
}
```

---

### 4. Download All Certificates as ZIP
- **Endpoint**: `GET /api/v1/jobs/{job_id}/download-zip`
- **Status**: `200 OK`
- **Content-Type**: `application/zip`

```bash
curl -X GET "http://localhost:8000/api/v1/jobs/72d527ec-761b-4b91-9670-8cdbdac9cdae/download-zip" \
     -o "certificates_batch.zip"
```

---

### 5. Download Individual Certificate PDF
- **Endpoint**: `GET /api/v1/certificates/{certificate_id}/download`
- **Query Parameter**: `inline=true` (optional, to view directly in browser)

```bash
curl -X GET "http://localhost:8000/api/v1/certificates/30555a3b-6c68-41af-98a4-f01dd41fb070/download" \
     -o "Sarah_Connor_Certificate.pdf"
```

---

### 6. Verify Certificate Authenticity
- **Endpoint**: `GET /api/v1/certificates/verify/{identifier}`
- Accepts either `certificate_number` (e.g. `CERT-20261008-4FB42ECF`) or `verification_code`.

```bash
curl -X GET "http://localhost:8000/api/v1/certificates/verify/CERT-20261008-4FB42ECF"
```

#### Example Response:
```json
{
  "valid": true,
  "certificate_number": "CERT-20261008-4FB42ECF",
  "recipient_name": "Sarah Connor",
  "recipient_email": "sarah.connor@example.com",
  "event_name": "Executive Masterclass in Generative AI",
  "organization_name": "DeepMind Academy",
  "issuer_name": "Dr. Alan Turing",
  "issuer_title": "Director of Research",
  "issue_date": "October 8, 2026",
  "grade_or_score": "High Distinction (98%)",
  "verification_code": "5AF9EBA1C04DE2B3",
  "sha256_hash": "ac9cd221ee7209e33567948349b3e454fc5898c3c52eef340cd84d9860d33630",
  "issued_at": "2026-10-08T05:38:12Z",
  "verification_message": "Certificate is authentic, verified, and issued by an authorized organization."
}
```

---

### 7. List All Jobs
- **Endpoint**: `GET /api/v1/jobs?skip=0&limit=20`

```bash
curl -X GET "http://localhost:8000/api/v1/jobs?skip=0&limit=20"
```

---

## Interview Q&A / Architecture Justifications

### Q1: Why did you choose asynchronous background processing over synchronous generation?
**Answer**:
Generating 500 or 1,000 PDF certificates involves file I/O, canvas rendering, and QR generation, which may take tens of seconds. Running this synchronously would block the HTTP worker thread, exceed HTTP client gateway timeouts (such as Nginx 60s timeout), and degrade overall server responsiveness. By returning `202 Accepted` with a `job_id`, client requests complete in milliseconds, and the client can poll progress or subscribe via webhooks/WebSockets.

### Q2: How does the system handle failures during bulk generation?
**Answer**:
Each recipient is processed inside an isolated `try-except` block within the background loop. If recipient #4 fails due to an edge case or corrupt character encoding, that recipient is updated to status `FAILED` with an explicit `error_message`, while recipients #1–3 and #5+ continue processing. The job status reflects this by transitioning to `PARTIALLY_FAILED` instead of `COMPLETED` or `FAILED`, enabling clear auditing.

### Q3: How can this system be scaled to handle 100,000+ recipients?
**Answer**:
1. **Task Queue Migration**: Replace in-process `BackgroundTasks` with **Celery** or **ARQ** backed by **Redis** or **RabbitMQ**.
2. **Batch Chunking**: Split jobs into batches of 100 recipients and distribute them across multiple Celery worker nodes concurrently.
3. **Cloud Storage**: Store PDF artifacts on an S3/GCS bucket with presigned download URLs rather than local storage.
4. **Database Indexing**: Add database indexes on `job_id`, `recipient_id`, `certificate_number`, and `verification_code` (already implemented in this codebase).

### Q4: Why ReportLab instead of HTML-to-PDF (like WeasyPrint or Puppeteer)?
**Answer**:
1. **Speed & Lightweight Footprint**: ReportLab runs in pure Python with C-accelerated primitives, without requiring an external headless Chrome browser or complex system GTK libraries.
2. **Vector Precision**: All borders, text, and vector rosette paths remain sharp regardless of print scaling.
3. **Security**: Avoids SSRF or arbitrary local file inclusion vulnerabilities associated with rendering user-supplied HTML.
