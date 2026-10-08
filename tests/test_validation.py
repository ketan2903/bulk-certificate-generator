import io

def test_create_job_missing_event_name(client):
    payload = {
        "event_name": "",
        "recipients": [{"name": "Jane", "email": "jane@example.com"}]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422

def test_create_job_empty_recipients_list(client):
    payload = {
        "event_name": "Web Dev Workshop",
        "recipients": []
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422

def test_create_job_invalid_email_format(client):
    payload = {
        "event_name": "Web Dev Workshop",
        "recipients": [{"name": "Jane Doe", "email": "not-an-email"}]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422

def test_create_job_blank_recipient_name(client):
    payload = {
        "event_name": "Web Dev Workshop",
        "recipients": [{"name": "   ", "email": "valid@example.com"}]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422

def test_csv_upload_validation(client):
    # Missing required 'email' column
    bad_csv = "name,grade\nJohn Doe,95\n"
    response = client.post(
        "/api/v1/jobs/upload-csv",
        data={"event_name": "CSV Workshop"},
        files={"file": ("test.csv", io.BytesIO(bad_csv.encode("utf-8")), "text/csv")}
    )
    assert response.status_code == 422

def test_csv_upload_non_csv_file(client):
    response = client.post(
        "/api/v1/jobs/upload-csv",
        data={"event_name": "CSV Workshop"},
        files={"file": ("test.txt", io.BytesIO(b"random text"), "text/plain")}
    )
    assert response.status_code == 400
