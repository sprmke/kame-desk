from __future__ import annotations

from io import BytesIO
from typing import Any

from app.models import Clinic, DoctorProfile, Patient, Prescription


def render_prescription_pdf(
    clinic: Clinic,
    patient: Patient,
    doctor: DoctorProfile,
    doctor_name: str,
    prescription: Prescription,
    override_reason: str | None,
    conflict_flags: list[dict[str, Any]] | None,
) -> bytes:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - inch

    from app.services.pdf_brand import draw_letterhead_accent

    c.setFont("Helvetica-Bold", 14)
    c.drawString(inch, y, clinic.name)
    y -= 0.12 * inch
    draw_letterhead_accent(c, inch, y, width - 2 * inch, clinic.brand_color)
    y -= 0.12 * inch
    c.setFont("Helvetica", 10)
    if clinic.address:
        c.drawString(inch, y, clinic.address)
        y -= 0.16 * inch

    c.setFont("Helvetica-Bold", 12)
    y -= 0.2 * inch
    c.drawString(inch, y, "Prescription")
    y -= 0.18 * inch
    c.setFont("Helvetica", 10)
    c.drawString(inch, y, f"Patient: {patient.full_name}")
    y -= 0.16 * inch
    c.drawString(inch, y, f"Prescriber: {doctor_name}")
    y -= 0.16 * inch
    c.drawString(inch, y, f"PRC License: {doctor.prc_license_number or '—'}")
    y -= 0.24 * inch

    for item in prescription.items:
        if y < inch * 1.5:
            c.showPage()
            y = height - inch
        line = f"{item.drug_name}"
        if item.dosage:
            line += f" {item.dosage}"
        if item.form:
            line += f" ({item.form})"
        c.setFont("Helvetica-Bold", 11)
        c.drawString(inch, y, line)
        y -= 0.16 * inch
        c.setFont("Helvetica", 10)
        sig = []
        if item.frequency:
            sig.append(item.frequency)
        if item.duration:
            sig.append(item.duration)
        if item.quantity:
            sig.append(f"Qty: {item.quantity}")
        if sig:
            c.drawString(inch + 0.1 * inch, y, " · ".join(sig))
            y -= 0.14 * inch
        if item.special_instructions:
            c.drawString(inch + 0.1 * inch, y, item.special_instructions)
            y -= 0.14 * inch
        y -= 0.1 * inch

    if override_reason:
        y -= 0.1 * inch
        c.setFont("Helvetica-Bold", 10)
        c.drawString(inch, y, "Safety override:")
        y -= 0.14 * inch
        c.setFont("Helvetica", 10)
        for line in _wrap(override_reason, 90):
            c.drawString(inch, y, line)
            y -= 0.14 * inch

    if conflict_flags:
        y -= 0.1 * inch
        c.setFont("Helvetica", 9)
        for flag in conflict_flags:
            for line in _wrap(flag.get("message", ""), 90):
                if y < inch:
                    c.showPage()
                    y = height - inch
                c.drawString(inch, y, line)
                y -= 0.12 * inch

    y -= 0.3 * inch
    if y < inch:
        c.showPage()
        y = height - inch
    c.setFont("Helvetica", 10)
    if doctor.signature_image_key:
        c.drawString(inch, y, "Signed electronically")
    else:
        c.drawString(inch, y, "Signature: _________________________")

    c.showPage()
    c.save()
    return buffer.getvalue()


def _wrap(text: str, width: int) -> list[str]:
    if not text:
        return [""]
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]
