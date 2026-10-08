import io
import zipfile

def test_download_individual_certificate(client):
    payload = {
        "event_name": "Python Advanced Mastery",
        "recipients": [{"name": "Guido van Rossum", "email": "guido@python.org"}]
    }

    create_resp = client.post("/api/v1/jobs", json=payload)
    job_id = create_resp.json()["id"]

    job_detail = client.get(f"/api/v1/jobs/{job_id}").json()
    cert_id = job_detail["recipients"][0]["certificate_id"]

    # 1. Get metadata
    meta_resp = client.get(f"/api/v1/certificates/{cert_id}")
    assert meta_resp.status_code == 200
    assert meta_resp.json()["id"] == cert_id

    # 2. Download PDF
    download_resp = client.get(f"/api/v1/certificates/{cert_id}/download")
    assert download_resp.status_code == 200
    assert download_resp.headers["content-type"] == "application/pdf"
    assert download_resp.content.startswith(b"%PDF-")

def test_download_nonexistent_certificate_returns_404(client):
    resp = client.get("/api/v1/certificates/non-existent-id/download")
    assert resp.status_code == 404

def test_download_job_zip_archive(client):
    payload = {
        "event_name": "Distributed Systems",
        "recipients": [
            {"name": "Leslie Lamport", "email": "leslie@example.com"},
            {"name": "Barbara Liskov", "email": "barbara@example.com"},
        ]
    }

    create_resp = client.post("/api/v1/jobs", json=payload)
    job_id = create_resp.json()["id"]

    zip_resp = client.get(f"/api/v1/jobs/{job_id}/download-zip")
    assert zip_resp.status_code == 200
    assert zip_resp.headers["content-type"] == "application/zip"

    # Verify zip content
    with zipfile.ZipFile(io.BytesIO(zip_resp.content)) as z:
        namelist = z.namelist()
        assert len(namelist) == 2
        for name in namelist:
            assert name.endswith(".pdf")
