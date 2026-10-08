from app.models.job import GenerationJob, JobStatus
from app.models.recipient import Recipient

def test_create_generation_job_success(client, db_session):
    payload = {
        "event_name": "Full-Stack AI Engineering Bootcamp",
        "organization_name": "AI Institute",
        "issuer_name": "Dr. Geoffrey Hinton",
        "issuer_title": "Chief Scientist",
        "recipients": [
            {
                "name": "Alice Johnson",
                "email": "alice@example.com",
                "issue_date": "2026-10-08",
                "grade_or_score": "95%",
                "custom_message": "Excellence in Deep Learning"
            },
            {
                "name": "Bob Smith",
                "email": "bob@example.com",
                "issue_date": "2026-10-08",
                "grade_or_score": "88%"
            }
        ]
    }

    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 202
    data = response.json()

    assert "id" in data
    assert data["event_name"] == "Full-Stack AI Engineering Bootcamp"
    assert data["organization_name"] == "AI Institute"
    assert data["total_recipients"] == 2
    assert data["status"] in ["PENDING", "PROCESSING", "COMPLETED"]

    # Verify database persistence
    job = db_session.query(GenerationJob).filter(GenerationJob.id == data["id"]).first()
    assert job is not None
    assert job.event_name == "Full-Stack AI Engineering Bootcamp"
    assert len(job.recipients) == 2

def test_list_jobs_endpoint(client):
    # Create multiple jobs
    for i in range(3):
        client.post("/api/v1/jobs", json={
            "event_name": f"Event {i}",
            "recipients": [{"name": f"User {i}", "email": f"user{i}@example.com"}]
        })

    response = client.get("/api/v1/jobs")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 3
    assert len(data["items"]) >= 3
