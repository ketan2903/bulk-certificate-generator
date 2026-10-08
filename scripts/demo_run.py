import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import json
from fastapi.testclient import TestClient
from app.main import app

def main():
    client = TestClient(app)
    
    print("=" * 60)
    print(" BULK CERTIFICATE GENERATOR - DEMO RUN")
    print("=" * 60)
    
    # 1. Load sample JSON
    with open("sample_data/sample_recipients.json", "r", encoding="utf-8") as f:
        payload = json.load(f)
        
    print(f"\n[1] Submitting bulk generation job for {len(payload['recipients'])} recipients...")
    create_resp = client.post("/api/v1/jobs", json=payload)
    print(f"Status Code: {create_resp.status_code}")
    job_summary = create_resp.json()
    job_id = job_summary["id"]
    print(f"Job ID: {job_id}")
    
    # 2. Query job status
    print(f"\n[2] Checking status for Job {job_id}...")
    status_resp = client.get(f"/api/v1/jobs/{job_id}")
    detail = status_resp.json()
    print(f"Status: {detail['status']}")
    print(f"Total: {detail['total_recipients']}, Success: {detail['successful_recipients']}, Failed: {detail['failed_recipients']}")
    print(f"Progress: {detail['progress_percentage']}%")
    print(f"ZIP Download URL: {detail['download_all_zip_url']}")
    
    # 3. Inspect generated certificates
    print("\n[3] Generated Certificates:")
    for r in detail["recipients"]:
        print(f" - {r['name']} <{r['email']}> -> {r['certificate_number']} (Download: {r['download_url']})")
        
    # 4. Test Verification
    first_cert = detail["recipients"][0]
    cert_num = first_cert["certificate_number"]
    print(f"\n[4] Verifying certificate '{cert_num}'...")
    verify_resp = client.get(f"/api/v1/certificates/verify/{cert_num}")
    verify_data = verify_resp.json()
    print(f"Verified: {verify_data['valid']}")
    print(f"Recipient: {verify_data['recipient_name']}")
    print(f"Event: {verify_data['event_name']}")
    print(f"SHA-256 Hash: {verify_data['sha256_hash']}")
    
    # 5. Test ZIP Download
    print(f"\n[5] Downloading ZIP archive for job...")
    zip_resp = client.get(f"/api/v1/jobs/{job_id}/download-zip")
    print(f"ZIP Response Status: {zip_resp.status_code}, Size: {len(zip_resp.content)} bytes")
    
    print("\n" + "=" * 60)
    print(" DEMO COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    main()
