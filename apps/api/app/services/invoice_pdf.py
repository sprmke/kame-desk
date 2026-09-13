from __future__ import annotations

from decimal import Decimal
from io import BytesIO

from app.models import Clinic, Invoice, Patient


def render_invoice_pdf(clinic: Clinic, patient: Patient, invoice: Invoice) -> bytes:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - inch

    from app.services.pdf_brand import draw_letterhead_accent

    bir = clinic.bir_compliance_config or {}

    c.setFont("Helvetica-Bold", 14)
    c.drawString(inch, y, str(bir.get("registered_name") or clinic.name))
    y -= 0.12 * inch
    draw_letterhead_accent(c, inch, y, width - 2 * inch, clinic.brand_color)
    y -= 0.12 * inch
    c.setFont("Helvetica", 10)
    address = bir.get("registered_address") or clinic.address
    if address:
        c.drawString(inch, y, str(address))
        y -= 0.16 * inch
    if bir.get("tin"):
        c.drawString(inch, y, f"TIN: {bir['tin']}")
        y -= 0.16 * inch
    if bir.get("compliance_mode") in ("ptu", "cas") and bir.get("accreditation_number"):
        label = "Permit to Use" if bir["compliance_mode"] == "ptu" else "CAS Accreditation"
        c.drawString(inch, y, f"{label} No. {bir['accreditation_number']}")
        y -= 0.16 * inch
    c.setFont("Helvetica-Oblique", 8)
    if bir.get("vat_registered"):
        c.drawString(inch, y, "VAT Registered")
    else:
        c.drawString(inch, y, "Non-VAT. This document is not valid for claim of input tax.")
    y -= 0.16 * inch

    c.setFont("Helvetica-Bold", 12)
    y -= 0.2 * inch
    title = "Official Receipt" if invoice.invoice_number else "Invoice"
    c.drawString(inch, y, title)
    y -= 0.18 * inch
    c.setFont("Helvetica", 10)
    if invoice.invoice_number:
        c.drawString(inch, y, f"No. {invoice.invoice_number}")
        y -= 0.16 * inch
    c.drawString(inch, y, f"Patient: {patient.full_name}")
    y -= 0.16 * inch
    if invoice.issued_at:
        c.drawString(
            inch,
            y,
            f"Date: {invoice.issued_at.astimezone().strftime('%Y-%m-%d %H:%M')}",
        )
        y -= 0.24 * inch

    c.setFont("Helvetica-Bold", 10)
    c.drawString(inch, y, "Description")
    c.drawString(width - 2 * inch, y, "Amount")
    y -= 0.16 * inch
    c.setFont("Helvetica", 10)

    for item in invoice.line_items:
        if y < inch * 1.5:
            c.showPage()
            y = height - inch
        c.drawString(inch, y, item.description[:60])
        c.drawRightString(width - inch, y, _fmt(item.amount))
        y -= 0.14 * inch
        if item.hmo_claim_reference:
            c.setFont("Helvetica", 8)
            c.drawString(inch + 0.1 * inch, y, f"HMO ref: {item.hmo_claim_reference}")
            y -= 0.12 * inch
            c.setFont("Helvetica", 10)

    y -= 0.1 * inch
    if bir.get("vat_registered") and invoice.total > Decimal("0"):
        vat_rate = Decimal("0.12")
        vatable_sales = (invoice.total / (Decimal("1") + vat_rate)).quantize(Decimal("0.01"))
        vat_amount = invoice.total - vatable_sales
        c.setFont("Helvetica", 9)
        c.drawString(inch, y, "VATable Sales")
        c.drawRightString(width - inch, y, _fmt(vatable_sales))
        y -= 0.14 * inch
        c.drawString(inch, y, "VAT (12%)")
        c.drawRightString(width - inch, y, _fmt(vat_amount))
        y -= 0.18 * inch

    c.setFont("Helvetica-Bold", 11)
    c.drawString(inch, y, "Total")
    c.drawRightString(width - inch, y, _fmt(invoice.total))
    y -= 0.2 * inch

    paid = sum((p.amount for p in invoice.payments), Decimal("0"))
    if paid > Decimal("0"):
        c.setFont("Helvetica", 10)
        c.drawString(inch, y, f"Paid: {_fmt(paid)}")
        y -= 0.16 * inch
        balance = invoice.total - paid
        if balance > Decimal("0"):
            c.drawString(inch, y, f"Balance: {_fmt(balance)}")

    c.showPage()
    c.save()
    return buffer.getvalue()


def _fmt(amount: Decimal) -> str:
    return f"PHP {amount:,.2f}"
