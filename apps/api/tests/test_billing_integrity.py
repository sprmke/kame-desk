from decimal import Decimal

import pytest
from httpx import AsyncClient

from tests.test_billing import _create_appointment, _create_patient, _draft_invoice
from tests.test_patients_appointments import _setup_clinic


def _pdf_stubs(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.invoice_service.upload_object_bytes",
        lambda key, body, ct: key,
    )
    monkeypatch.setattr(
        "app.services.invoice_pdf.render_invoice_pdf",
        lambda *args, **kwargs: b"%PDF-1.4",
    )


@pytest.mark.asyncio
async def test_credit_note_and_clinic_invoice_list(client: AsyncClient, monkeypatch):
    _pdf_stubs(monkeypatch)
    ctx = await _setup_clinic(client)
    patient_id = await _create_patient(client, ctx["headers"])
    appt_id = await _create_appointment(client, ctx["headers"], patient_id, ctx["doctor_id"])
    invoice_id = await _draft_invoice(client, ctx["headers"], patient_id, appt_id)
    issued = await client.post(
        f"/api/v1/invoices/{invoice_id}/issue",
        headers=ctx["headers"],
    )
    assert issued.status_code == 200
    total = Decimal(issued.json()["total"])
    paid = await client.post(
        f"/api/v1/invoices/{invoice_id}/payments",
        headers=ctx["headers"],
        json={"method": "cash", "amount": str(total)},
    )
    assert paid.status_code == 200

    credit = await client.post(
        f"/api/v1/invoices/{invoice_id}/credit-notes",
        headers=ctx["headers"],
        json={"kind": "refund", "amount": str(total / 2), "reason": "Overcharge"},
    )
    assert credit.status_code == 200
    assert Decimal(credit.json()["amount_credited"]) == total / 2
    assert credit.json()["credit_notes"][0]["credit_number"] == "CN-000001"

    too_much = await client.post(
        f"/api/v1/invoices/{invoice_id}/credit-notes",
        headers=ctx["headers"],
        json={"kind": "refund", "amount": str(total), "reason": "Too much"},
    )
    assert too_much.status_code == 400

    listed = await client.get(
        "/api/v1/invoices",
        headers=ctx["headers"],
        params={"q": "Bill"},
    )
    assert listed.status_code == 200
    assert any(row["id"] == invoice_id for row in listed.json()["items"])

    csv = await client.get(
        "/api/v1/invoices/export",
        headers=ctx["headers"],
    )
    assert csv.status_code == 200
    assert "invoice_number" in csv.text
    assert "OR-000001" in csv.text


@pytest.mark.asyncio
async def test_insurance_claim_lifecycle(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={
            "full_name": "Claim Patient",
            "data_processing_consent": True,
            "insurance_info": {"provider": "Maxicare", "member_id": "M-1"},
        },
    )
    patient_id = patient.json()["id"]
    created = await client.post(
        "/api/v1/claims",
        headers=ctx["headers"],
        json={
            "patient_id": patient_id,
            "provider": "Maxicare",
            "member_id": "M-1",
            "amount": "1500.00",
        },
    )
    assert created.status_code == 200
    assert created.json()["status"] == "draft"
    claim_id = created.json()["id"]

    patched = await client.patch(
        f"/api/v1/claims/{claim_id}",
        headers=ctx["headers"],
        json={"status": "submitted"},
    )
    assert patched.status_code == 200
    assert patched.json()["status"] == "submitted"

    listed = await client.get(
        "/api/v1/claims",
        headers=ctx["headers"],
        params={"status": "submitted"},
    )
    assert listed.status_code == 200
    assert listed.json()["items"][0]["id"] == claim_id
