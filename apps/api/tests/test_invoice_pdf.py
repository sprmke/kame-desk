import uuid
from datetime import UTC, datetime
from decimal import Decimal
from io import BytesIO

import pytest
from pypdf import PdfReader

from app.models import Clinic, Invoice, InvoiceLineItem, Patient
from app.services.invoice_pdf import render_invoice_pdf


def _clinic(**overrides) -> Clinic:
    clinic = Clinic(
        id=uuid.uuid4(),
        name="Santos Family Clinic",
        slug="santos-family-clinic",
        address="Old Address, Manila",
    )
    for key, value in overrides.items():
        setattr(clinic, key, value)
    return clinic


def _patient() -> Patient:
    return Patient(id=uuid.uuid4(), full_name="Maria Santos")


def _invoice(total: Decimal = Decimal("1120.00")) -> Invoice:
    invoice = Invoice(
        id=uuid.uuid4(),
        invoice_number="OR-000001",
        total=total,
        subtotal=total,
        issued_at=datetime(2026, 1, 15, 9, 30, tzinfo=UTC),
    )
    invoice.line_items = [
        InvoiceLineItem(
            id=uuid.uuid4(),
            description="Consultation",
            amount=total,
            unit_price=total,
        )
    ]
    invoice.payments = []
    return invoice


def _pdf_text(data: bytes) -> str:
    reader = PdfReader(BytesIO(data))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def test_invoice_pdf_falls_back_to_clinic_fields_when_no_bir_config():
    clinic = _clinic(bir_compliance_config=None)
    pdf = render_invoice_pdf(clinic, _patient(), _invoice())
    text = _pdf_text(pdf)

    assert "Santos Family Clinic" in text
    assert "Old Address, Manila" in text
    assert "TIN" not in text
    assert "Non-VAT" in text


def test_invoice_pdf_renders_tin_and_registered_identity():
    clinic = _clinic(
        bir_compliance_config={
            "tin": "123-456-789-000",
            "registered_name": "Santos Family Clinic Corp.",
            "registered_address": "123 Rizal St, Quezon City",
            "vat_registered": False,
            "compliance_mode": "not_yet_accredited",
        }
    )
    pdf = render_invoice_pdf(clinic, _patient(), _invoice())
    text = _pdf_text(pdf)

    assert "Santos Family Clinic Corp." in text
    assert "123 Rizal St, Quezon City" in text
    assert "TIN: 123-456-789-000" in text
    assert "Non-VAT" in text


def test_invoice_pdf_renders_ptu_accreditation_number():
    clinic = _clinic(
        bir_compliance_config={
            "compliance_mode": "ptu",
            "accreditation_number": "PTU-2026-00042",
            "vat_registered": False,
        }
    )
    pdf = render_invoice_pdf(clinic, _patient(), _invoice())
    text = _pdf_text(pdf)

    assert "Permit to Use No. PTU-2026-00042" in text


def test_invoice_pdf_renders_cas_accreditation_number():
    clinic = _clinic(
        bir_compliance_config={
            "compliance_mode": "cas",
            "accreditation_number": "CAS-2026-00099",
            "vat_registered": False,
        }
    )
    pdf = render_invoice_pdf(clinic, _patient(), _invoice())
    text = _pdf_text(pdf)

    assert "CAS Accreditation No. CAS-2026-00099" in text


def test_invoice_pdf_renders_vat_breakdown_when_vat_registered():
    clinic = _clinic(bir_compliance_config={"vat_registered": True})
    pdf = render_invoice_pdf(clinic, _patient(), _invoice(total=Decimal("1120.00")))
    text = _pdf_text(pdf)

    assert "VAT Registered" in text
    assert "VATable Sales" in text
    assert "VAT (12%)" in text
    assert "PHP 1,000.00" in text
    assert "PHP 120.00" in text


def test_invoice_pdf_skips_vat_breakdown_when_not_vat_registered():
    clinic = _clinic(bir_compliance_config={"vat_registered": False})
    pdf = render_invoice_pdf(clinic, _patient(), _invoice())
    text = _pdf_text(pdf)

    assert "VATable Sales" not in text
    assert "Non-VAT. This document is not valid for claim of input tax." in text


@pytest.mark.parametrize("total", [Decimal("0"), Decimal("0.00")])
def test_invoice_pdf_skips_vat_breakdown_for_zero_total(total: Decimal):
    clinic = _clinic(bir_compliance_config={"vat_registered": True})
    pdf = render_invoice_pdf(clinic, _patient(), _invoice(total=total))
    text = _pdf_text(pdf)

    assert "VATable Sales" not in text
