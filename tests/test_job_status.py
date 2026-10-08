import time
from app.services.background_worker import process_bulk_certificate_job
from app.models.job import JobStatus

def test_job_status_and_progress_flow(client, db_session):
    payload = {
        "event_name": "Cloud Native Architecture",
        "recipients": [
            {"name": "Dev One", "email": "dev1@example.com"},
            {"name": "Dev Two", "email": "dev2@example.com"}
        ]
    }

    # 1. Create job
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 202
    job_id = response.json()["id"]

    # In TestClient, background tasks run synchronously during/after request
    # Let's query status
    status_resp = client.get(f"/api/v1/jobs/{job_id}")
    assert status_resp.status_code == 200
    data = status_resp.json()

    assert data["id"] == job_id
    assert data["total_recipients"] == 2
    assert data["successful_recipients"] == 2
    assert data["failed_recipients"] == 0
    assert data["progress_percentage"] == 100.0
    assert data["status"] == "COMPLETED"
    assert len(data["recipients"]) == 2

    # Check that each recipient has certificate details and download link
    for r in data["recipients"]:
        assert r["status"] == "SUCCESS"
        assert r["certificate_id"] is not None
        assert r["certificate_number"] is not None
        assert r["download_url"] is not None
