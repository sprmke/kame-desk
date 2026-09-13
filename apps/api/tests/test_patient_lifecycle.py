"""End-to-end patient lifecycle: book → visit → SOAP → Rx → bill → pay."""

import pytest
from httpx import AsyncClient

from tests.test_patients_appointments import _setup_clinic

SOAP_BODY = {
    "subjective": "Follow-up cough",
    "objective": "Clear lungs",
    "assessment": "Resolved URTI",
    "plan": "Continue rest",
    "specialty_template_key": "general",
}


@pytest.mark.asyncio
async def test_full_patient_lifecycle(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(
        "app.services.invoice_service.upload_object_bytes",
        lambda key, body, ct: key,
    )
    monkeypatch.setattr(
        "app.services.invoice_pdf.render_invoice_pdf",
        lambda *args, **kwargs: b"%PDF-1.4",
    )
    monkeypatch.setattr(
        "app.services.prescription_service.upload_object_bytes",
        lambda key, body, ct: key,
    )
    monkeypatch.setattr(
        "app.services.prescription_pdf.render_prescription_pdf",
        lambda **kwargs: b"%PDF-1.4",
    )

    ctx = await _setup_clinic(client)
    headers = ctx["headers"]

    patient = await client.post(
        "/api/v1/patients",
        headers=headers,
        json={"full_name": "Lifecycle Patient", "data_processing_consent": True},
    )
    assert patient.status_code == 200
    patient_id = patient.json()["id"]

    appt = await client.post(
        "/api/v1/appointments",
        headers=headers,
        json={
            "patient_id": patient_id,
            "doctor_id": ctx["doctor_id"],
            "scheduled_start": "2026-10-20T10:00:00+08:00",
            "scheduled_end": "2026-10-20T10:30:00+08:00",
        },
    )
    assert appt.status_code == 200
    appt_id = appt.json()["id"]

    for status in ("Arrived", "In Consultation", "Completed"):
        visit = await client.post(
            f"/api/v1/appointments/{appt_id}/visit-status",
            headers=headers,
            json={"visit_status": status},
        )
        assert visit.status_code == 200

    soap = await client.post(
        f"/api/v1/appointments/{appt_id}/soap-notes",
        headers=headers,
        json=SOAP_BODY,
    )
    assert soap.status_code == 200
    assert soap.json()["version_number"] == 1

    rx = await client.post(
        f"/api/v1/patients/{patient_id}/prescriptions",
        headers=headers,
        json={"items": [{"drug_name": "Paracetamol", "dosage": "500mg"}]},
    )
    assert rx.status_code == 200
    rx_id = rx.json()["id"]
    issued_rx = await client.post(
        f"/api/v1/prescriptions/{rx_id}/issue",
        headers=headers,
        json={},
    )
    assert issued_rx.status_code == 200

    invoice = await client.post(
        f"/api/v1/patients/{patient_id}/invoices",
        headers=headers,
        json={
            "appointment_id": appt_id,
            "line_items": [
                {
                    "description": "Consultation",
                    "quantity": "1",
                    "unit_price": "500.00",
                }
            ],
        },
    )
    assert invoice.status_code == 200
    invoice_id = invoice.json()["id"]

    issued_inv = await client.post(
        f"/api/v1/invoices/{invoice_id}/issue",
        headers=headers,
        json={},
    )
    assert issued_inv.status_code == 200

    payment = await client.post(
        f"/api/v1/invoices/{invoice_id}/payments",
        headers=headers,
        json={"amount": "500.00", "method": "cash"},
    )
    assert payment.status_code == 200

    balance = await client.get(
        f"/api/v1/patients/{patient_id}/balance",
        headers=headers,
    )
    assert balance.status_code == 200
    assert balance.json()["outstanding_balance"] in ("0", "0.00", 0, 0.0)
