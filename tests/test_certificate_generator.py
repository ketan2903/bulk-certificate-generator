import os
from pathlib import Path
from app.services.certificate_generator import CertificateGenerator

def test_certificate_pdf_generation_direct(temp_storage):
    generator = CertificateGenerator(output_dir=temp_storage / "certificates")
    
    result = generator.generate_certificate(
        recipient_name="Alexander Hamilton",
        recipient_email="alexander@example.com",
        event_name="Foundations of Financial Economics",
        certificate_number="CERT-20261008-TEST001",
        verification_code="ABCDEF1234567890",
        organization_name="Academy of Treasury",
        issuer_name="George Washington",
        issuer_title="President",
        issue_date="October 8, 2026",
        grade_or_score="Distinction (99%)",
        custom_message="Outstanding performance in state economics."
    )

    assert os.path.exists(result["file_path"])
    assert result["file_size_bytes"] > 1000
    assert len(result["sha256_hash"]) == 64

    # Verify that file has valid PDF magic header
    with open(result["file_path"], "rb") as f:
        header = f.read(5)
        assert header == b"%PDF-"
