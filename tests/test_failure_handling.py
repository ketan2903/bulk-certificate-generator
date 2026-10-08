from app.models.job import JobStatus
from app.models.recipient import RecipientStatus

def test_individual_recipient_failure_isolation(client):
    """
    Test that an unexpected generation failure for one recipient (triggered via __FAIL__ name test hook)
    does not prevent other valid recipients in the same job from being generated successfully.
    """
    payload = {
        "event_name": "Resilient Systems Workshop",
        "recipients": [
            {"name": "Valid Recipient One", "email": "valid1@example.com"},
            {"name": "__FAIL__ Broken Recipient", "email": "fail@example.com"},
            {"name": "Valid Recipient Two", "email": "valid2@example.com"},
        ]
    }

    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 202
    job_id = response.json()["id"]

    # Check job status
    status_resp = client.get(f"/api/v1/jobs/{job_id}")
    assert status_resp.status_code == 200
    data = status_resp.json()

    assert data["total_recipients"] == 3
    assert data["successful_recipients"] == 2
    assert data["failed_recipients"] == 1
    assert data["status"] == "PARTIALLY_FAILED"
    assert "recipient(s) failed" in data["error_summary"]

    # Check recipient statuses individually
    recipients = {r["name"]: r for r in data["recipients"]}
    
    # Valid recipients must be SUCCESS with certificate links
    assert recipients["Valid Recipient One"]["status"] == "SUCCESS"
    assert recipients["Valid Recipient One"]["certificate_id"] is not None

    assert recipients["Valid Recipient Two"]["status"] == "SUCCESS"
    assert recipients["Valid Recipient Two"]["certificate_id"] is not None

    # Failed recipient must be FAILED with error message and no certificate
    assert recipients["__FAIL__ Broken Recipient"]["status"] == "FAILED"
    assert recipients["__FAIL__ Broken Recipient"]["certificate_id"] is None
    assert "Simulated generation failure" in recipients["__FAIL__ Broken Recipient"]["error_message"]

def test_all_recipients_failing_sets_job_status_failed(client):
    payload = {
        "event_name": "Failure Scenario Workshop",
        "recipients": [
            {"name": "__FAIL__ User A", "email": "a@example.com"},
            {"name": "__FAIL__ User B", "email": "b@example.com"},
        ]
    }

    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 202
    job_id = response.json()["id"]

    status_resp = client.get(f"/api/v1/jobs/{job_id}")
    data = status_resp.json()

    assert data["total_recipients"] == 2
    assert data["successful_recipients"] == 0
    assert data["failed_recipients"] == 2
    assert data["status"] == "FAILED"
