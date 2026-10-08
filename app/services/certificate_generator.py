import io
import math
from pathlib import Path
from typing import Optional
from datetime import datetime

import qrcode
from PIL import Image

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from app.config import settings
from app.utils.file_utils import sanitize_filename, calculate_sha256

class CertificateGenerator:
    """
    Generates high-resolution, vector-crisp PDF certificates using ReportLab.
    Features elegant double borders, decorative corner ornaments, gold rosette seal,
    dynamic typography, and scannable QR verification codes.
    """

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or settings.CERTIFICATES_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.page_width, self.page_height = landscape(letter) # 792 x 612 pt

    def _draw_borders_and_decorations(self, c: canvas.Canvas):
        w, h = self.page_width, self.page_height

        # 1. Subtle background fill
        c.setFillColor(colors.HexColor("#FDFCF7"))
        c.rect(0, 0, w, h, fill=True, stroke=False)

        # 2. Outer decorative border (Deep Navy)
        margin_outer = 24
        c.setStrokeColor(colors.HexColor("#0F2537"))
        c.setLineWidth(4)
        c.rect(margin_outer, margin_outer, w - 2 * margin_outer, h - 2 * margin_outer, fill=False, stroke=True)

        # 3. Inner border (Warm Gold)
        margin_inner = 32
        c.setStrokeColor(colors.HexColor("#C59B27"))
        c.setLineWidth(1.5)
        c.rect(margin_inner, margin_inner, w - 2 * margin_inner, h - 2 * margin_inner, fill=False, stroke=True)

        # 4. Corner decorative squares/diamonds
        corners = [
            (margin_outer + 12, margin_outer + 12),
            (w - margin_outer - 12, margin_outer + 12),
            (margin_outer + 12, h - margin_outer - 12),
            (w - margin_outer - 12, h - margin_outer - 12),
        ]
        c.setFillColor(colors.HexColor("#C59B27"))
        for cx, cy in corners:
            c.saveState()
            c.translate(cx, cy)
            c.rotate(45)
            c.rect(-4, -4, 8, 8, fill=True, stroke=False)
            c.restoreState()

    def _draw_seal(self, c: canvas.Canvas, center_x: float, center_y: float, radius: float = 32):
        """Draw a classic certificate gold seal badge."""
        c.saveState()
        
        # Rosette petals (star shape)
        num_points = 24
        c.setFillColor(colors.HexColor("#C59B27"))
        c.setStrokeColor(colors.HexColor("#9E7A18"))
        c.setLineWidth(0.8)
        
        path = c.beginPath()
        for i in range(num_points * 2):
            angle = i * (math.pi / num_points)
            r = radius if i % 2 == 0 else radius * 0.88
            px = center_x + r * math.cos(angle)
            py = center_y + r * math.sin(angle)
            if i == 0:
                path.moveTo(px, py)
            else:
                path.lineTo(px, py)
        path.close()
        c.drawPath(path, fill=True, stroke=True)

        # Inner golden disc
        c.setFillColor(colors.HexColor("#E5C158"))
        c.setStrokeColor(colors.HexColor("#0F2537"))
        c.setLineWidth(1)
        c.circle(center_x, center_y, radius * 0.76, fill=True, stroke=True)

        # Seal Text
        c.setFillColor(colors.HexColor("#0F2537"))
        c.setFont("Helvetica-Bold", 6.5)
        c.drawCentredString(center_x, center_y + 6, "OFFICIAL")
        c.drawCentredString(center_x, center_y - 2, "SEAL OF")
        c.drawCentredString(center_x, center_y - 10, "EXCELLENCE")

        # Star icon above/below
        c.setFont("Helvetica", 5)
        c.drawCentredString(center_x, center_y + 15, "★  ★  ★")

        c.restoreState()

    def _generate_qr_code(self, verification_url: str) -> io.BytesIO:
        """Generate a clean QR code image in-memory."""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=4,
            border=1,
        )
        qr.add_data(verification_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#0F2537", back_color="#FDFCF7")
        
        img_buffer = io.BytesIO()
        img.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        return img_buffer

    def generate_certificate(
        self,
        recipient_name: str,
        recipient_email: str,
        event_name: str,
        certificate_number: str,
        verification_code: str,
        organization_name: Optional[str] = None,
        issuer_name: Optional[str] = None,
        issuer_title: Optional[str] = None,
        issue_date: Optional[str] = None,
        grade_or_score: Optional[str] = None,
        custom_message: Optional[str] = None,
    ) -> dict:
        """
        Renders the PDF certificate for a recipient and returns metadata about the created file.
        """
        # Resolve fallbacks
        org_name = organization_name or settings.DEFAULT_ORGANIZATION
        signatory_name = issuer_name or settings.DEFAULT_SIGNATORY_NAME
        signatory_title = issuer_title or settings.DEFAULT_SIGNATORY_TITLE
        date_str = issue_date or datetime.now().strftime("%B %d, %Y")
        
        # File paths
        safe_name = sanitize_filename(f"{recipient_name}_{certificate_number}")
        file_name = f"{safe_name}.pdf"
        file_path = self.output_dir / file_name

        # Initialize ReportLab canvas
        c = canvas.Canvas(str(file_path), pagesize=landscape(letter))
        w, h = self.page_width, self.page_height

        # Draw decorative background & borders
        self._draw_borders_and_decorations(c)

        # 1. Organization Name (Top Header)
        c.setFillColor(colors.HexColor("#718096"))
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(w / 2.0, h - 68, org_name.upper())

        # 2. Main Title
        c.setFillColor(colors.HexColor("#0F2537"))
        c.setFont("Times-Bold", 30)
        c.drawCentredString(w / 2.0, h - 105, "CERTIFICATE OF ACHIEVEMENT")

        # Gold decorative horizontal accent lines
        c.setStrokeColor(colors.HexColor("#C59B27"))
        c.setLineWidth(1.5)
        c.line(w / 2.0 - 150, h - 118, w / 2.0 + 150, h - 118)

        # 3. Presentation Subtitle
        c.setFillColor(colors.HexColor("#4A5568"))
        c.setFont("Helvetica", 11)
        c.drawCentredString(w / 2.0, h - 148, "PROUDLY PRESENTED TO")

        # 4. Recipient Name
        c.setFillColor(colors.HexColor("#0F2537"))
        name_len = len(recipient_name)
        if name_len > 35:
            c.setFont("Times-BoldItalic", 22)
        elif name_len > 25:
            c.setFont("Times-BoldItalic", 26)
        else:
            c.setFont("Times-BoldItalic", 32)
        
        c.drawCentredString(w / 2.0, h - 192, recipient_name)

        # Recipient underline
        c.setStrokeColor(colors.HexColor("#C59B27"))
        c.setLineWidth(1)
        name_width = min(c.stringWidth(recipient_name), w - 200)
        c.line(w / 2.0 - name_width / 2.0 - 20, h - 202, w / 2.0 + name_width / 2.0 + 20, h - 202)

        # 5. Course / Event Description
        c.setFillColor(colors.HexColor("#4A5568"))
        c.setFont("Helvetica", 11)
        c.drawCentredString(w / 2.0, h - 232, "for successfully completing all curriculum requirements for")

        # 6. Event Name
        c.setFillColor(colors.HexColor("#1A365D"))
        event_len = len(event_name)
        if event_len > 45:
            c.setFont("Helvetica-Bold", 16)
        else:
            c.setFont("Helvetica-Bold", 19)
        c.drawCentredString(w / 2.0, h - 262, event_name)

        # 7. Optional Grade / Honors or Custom Message
        if grade_or_score and custom_message:
            c.setFillColor(colors.HexColor("#2D3748"))
            c.setFont("Helvetica-Oblique", 10.5)
            c.drawCentredString(w / 2.0, h - 290, f"Awarded with: {grade_or_score} — {custom_message}")
        elif grade_or_score:
            c.setFillColor(colors.HexColor("#2D3748"))
            c.setFont("Helvetica-Bold", 11)
            c.drawCentredString(w / 2.0, h - 290, f"Grade / Performance: {grade_or_score}")
        elif custom_message:
            c.setFillColor(colors.HexColor("#4A5568"))
            c.setFont("Helvetica-Oblique", 10.5)
            c.drawCentredString(w / 2.0, h - 290, f'"{custom_message}"')

        # 8. Center Official Rosette Seal
        self._draw_seal(c, w / 2.0, 115, radius=34)

        # 9. Left Side: Issue Date & Certificate ID
        c.setFillColor(colors.HexColor("#2D3748"))
        c.setFont("Helvetica-Bold", 10)
        c.drawString(60, 130, "DATE OF ISSUANCE")
        c.setFont("Helvetica", 10)
        c.drawString(60, 115, date_str)

        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(colors.HexColor("#718096"))
        c.drawString(60, 95, "CERTIFICATE ID")
        c.setFont("Helvetica", 8.5)
        c.drawString(60, 82, certificate_number)

        # 10. Right Side: Signature Line & Signatory
        sig_x = w - 240
        c.setStrokeColor(colors.HexColor("#718096"))
        c.setLineWidth(0.8)
        c.line(sig_x, 125, sig_x + 180, 125)

        c.setFillColor(colors.HexColor("#0F2537"))
        c.setFont("Times-Italic", 13)
        c.drawCentredString(sig_x + 90, 135, signatory_name)

        c.setFont("Helvetica-Bold", 9.5)
        c.drawCentredString(sig_x + 90, 110, signatory_name)

        c.setFillColor(colors.HexColor("#718096"))
        c.setFont("Helvetica", 8.5)
        c.drawCentredString(sig_x + 90, 97, signatory_title)

        # 11. QR Code for Verification (Bottom Left margin)
        verification_url = f"{settings.BASE_VERIFICATION_URL}/{certificate_number}"
        qr_stream = self._generate_qr_code(verification_url)
        qr_reader = ImageReader(qr_stream)
        c.drawImage(
            qr_reader,
            x=60,
            y=40,
            width=36,
            height=36,
            preserveAspectRatio=True
        )
        c.setFillColor(colors.HexColor("#A0AEC0"))
        c.setFont("Helvetica", 7)
        c.drawString(102, 60, f"Verify authenticity: {verification_code[:8]}...")
        c.drawString(102, 48, f"URL: {verification_url}")

        # Save and close canvas
        c.showPage()
        c.save()

        # Compute file stats and checksum
        file_size = file_path.stat().st_size
        sha256 = calculate_sha256(file_path)

        return {
            "file_name": file_name,
            "file_path": str(file_path.resolve()),
            "file_size_bytes": file_size,
            "sha256_hash": sha256,
        }

certificate_generator = CertificateGenerator()
