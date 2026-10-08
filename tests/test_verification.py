def test_verify_authentic_certificate_by_number(client):
    payload = {
        "event_name": "Cryptography & Information Security",
        "issuer_name": "Ron Rivest",
        "recipients": [{"name": "Claude Shannon", "email": "claude@bell-labs.com", "grade_or_score": "Top Honors"}]
    }

    create_resp = client.post("/api/v1/jobs", json=payload)
    job_id = create_resp.json()["id"]

    job_detail = client.get(f"/api/v1/jobs/{job_id}").json()
    cert_number = job_detail["recipients"][0]["certificate_number"]

    # Verify by cert number
    verify_resp = client.get(f"/api/v1/certificates/verify/{cert_number}")
    assert verify_resp.status_code == 200
    data = verify_resp.json()

    assert data["valid"] is True
    assert data["certificate_number"] == cert_number
    assert data["recipient_name"] == "Claude Shannon"
    assert data["event_name"] == "Cryptography & Information Security"
    assert data["issuer_name"] == "Ron Rivest"
    assert data["grade_or_score"] == "Top Honors"
    assert data["sha256_hash"] is not None

def test_verify_authentic_certificate_by_code(client):
    payload = {
        "event_name": "Network Protocols",
        "recipients": [{"name": "Vint Cerf", "email": "vint@internet.org"}]
    }

    create_resp = client.post("/api/v1/jobs", json=payload)
    job_id = create_resp.json()["id"]

    cert_id = client.get(f"/api/v1/jobs/{job_id}").json()["recipients"][0]["certificate_id"]
    cert_meta = client.get(f"/api/v1/certificates/{cert_id}").json()
    verification_code = cert_meta["verification_code"]

    # Verify by token/code
    verify_resp = client.get(f"/api/v1/certificates/verify/{verification_code}")
    assert verify_resp.status_code == 200
    assert verify_resp.json()["valid"] is True
    assert verify_resp.json()["recipient_name"] == "Vint Cerf"

def test_verify_fake_identifier_returns_invalid(client):
    verify_resp = client.get("/api/v1/certificates/verify/FAKE-NONEXISTENT-TOKEN-999")
    assert verify_resp.status_code == 200
    data = verify_resp.json()
    assert data["valid"] is False
    assert "No active certificate found" in data["verification_message"]
