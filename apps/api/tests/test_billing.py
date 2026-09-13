import asyncio
import re
import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient

from tests.test_patients_appointments import _setup_clinic


async def _create_patient(client: AsyncClient, headers: dict) -> str:
    res = await client.post(
        "/api/v1/patients",
        headers=headers,
        json={"full_name": "Bill Patient"},
    )
    assert res.status_code == 200
    return res.json()["id"]


async def _create_appointment(
    client: AsyncClient,
    headers: dict,
    patient_id: str,
    doctor_id: str,
) -> str:
    res = await client.post(
        "/api/v1/appointments",
        headers=headers,
        json={
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "scheduled_start": "2026-10-14T10:00:00+08:00",
            "scheduled_end": "2026-10-14T10:30:00+08:00",
        },
    )
    assert res.status_code == 200
    return res.json()["id"]


async def _draft_invoice(
    client: AsyncClient,
    headers: dict,
    patient_id: str,
    appointment_id: str | None = None,
    line_items: list | None = None,
) -> str:
    body: dict = {}
    if appointment_id:
        body["appointment_id"] = appointment_id
    if line_items:
        body["line_items"] = line_items
    res = await client.post(
        f"/api/v1/patients/{patient_id}/invoices",
        headers=headers,
        json=body,
    )
    assert res.status_code == 200
    return res.json()["id"]


@pytest.mark.asyncio
async def test_invoice_issue_and_partial_payment(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(
        "app.services.invoice_service.upload_object_bytes",
        lambda key, body, ct: key,
    )
    monkeypatch.setattr(
        "app.services.invoice_pdf.render_invoice_pdf",
        lambda *args, **kwargs: b"%PDF-1.4",
    )

    ctx = await _setup_clinic(client)
    patient_id = await _create_patient(client, ctx["headers"])
    appt_id = await _create_appointment(client, ctx["headers"], patient_id, ctx["doctor_id"])
    invoice_id = await _draft_invoice(client, ctx["headers"], patient_id, appt_id)

    issued = await client.post(
        f"/api/v1/invoices/{invoice_id}/issue",
        headers=ctx["headers"],
    )
    assert issued.status_code == 200
    data = issued.json()
    assert data["status"] == "issued"
    assert data["invoice_number"] == "OR-000001"
    total = Decimal(data["total"])

    pay1 = await client.post(
        f"/api/v1/invoices/{invoice_id}/payments",
        headers=ctx["headers"],
        json={"method": "cash", "amount": str(total / 2)},
    )
    assert pay1.status_code == 200
    assert pay1.json()["status"] == "partially_paid"

    pay2 = await client.post(
        f"/api/v1/invoices/{invoice_id}/payments",
        headers=ctx["headers"],
        json={"method": "gcash", "amount": str(total / 2)},
    )
    assert pay2.status_code == 200
    assert pay2.json()["status"] == "paid"

    balance = await client.get(
        f"/api/v1/patients/{patient_id}/balance",
        headers=ctx["headers"],
    )
    assert balance.status_code == 200
    assert Decimal(balance.json()["outstanding_balance"]) == Decimal("0")


@pytest.mark.asyncio
async def test_concurrent_invoice_numbering(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(
        "app.services.invoice_service.upload_object_bytes",
        lambda key, body, ct: key,
    )
    monkeypatch.setattr(
        "app.services.invoice_pdf.render_invoice_pdf",
        lambda *args, **kwargs: b"%PDF-1.4",
    )

    ctx = await _setup_clinic(client)
    patient_id = await _create_patient(client, ctx["headers"])

    ids = []
    for _ in range(3):
        inv_id = await _draft_invoice(
            client,
            ctx["headers"],
            patient_id,
            line_items=[
                {
                    "description": "Procedure",
                    "category": "procedure",
                    "quantity": "1",
                    "unit_price": "100.00",
                }
            ],
        )
        ids.append(inv_id)

    async def issue_one(inv_id: str):
        return await client.post(
            f"/api/v1/invoices/{inv_id}/issue",
            headers=ctx["headers"],
        )

    results = await asyncio.gather(*[issue_one(i) for i in ids])
    numbers = [r.json()["invoice_number"] for r in results]
    assert all(r.status_code == 200 for r in results)
    assert len(set(numbers)) == 3
    assert sorted(numbers) == ["OR-000001", "OR-000002", "OR-000003"]


@pytest.mark.asyncio
async def test_void_blocked_when_payments_exist(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(
        "app.services.invoice_service.upload_object_bytes",
        lambda key, body, ct: key,
    )
    monkeypatch.setattr(
        "app.services.invoice_pdf.render_invoice_pdf",
        lambda *args, **kwargs: b"%PDF-1.4",
    )

    ctx = await _setup_clinic(client)
    patient_id = await _create_patient(client, ctx["headers"])
    invoice_id = await _draft_invoice(
        client,
        ctx["headers"],
        patient_id,
        line_items=[
            {
                "description": "Consultation",
                "category": "consultation",
                "quantity": "1",
                "unit_price": "500.00",
            }
        ],
    )
    await client.post(
        f"/api/v1/invoices/{invoice_id}/issue",
        headers=ctx["headers"],
    )
    await client.post(
        f"/api/v1/invoices/{invoice_id}/payments",
        headers=ctx["headers"],
        json={"method": "cash", "amount": "100.00"},
    )
    voided = await client.post(
        f"/api/v1/invoices/{invoice_id}/void",
        headers=ctx["headers"],
        json={"reason": "Mistake"},
    )
    assert voided.status_code == 400


@pytest.mark.asyncio
async def test_doctor_cannot_view_other_doctors_invoice(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(
        "app.services.invoice_service.upload_object_bytes",
        lambda key, body, ct: key,
    )
    monkeypatch.setattr(
        "app.services.invoice_pdf.render_invoice_pdf",
        lambda *args, **kwargs: b"%PDF-1.4",
    )
    captured: dict[str, str] = {}

    def fake_send(_email: str, accept_url: str, _clinic: str) -> None:
        captured["url"] = accept_url

    monkeypatch.setattr("app.services.clinic_service.send_invitation_email", fake_send)

    ctx = await _setup_clinic(client)
    clinic_id = ctx["clinic_id"]

    patient_id = await _create_patient(client, ctx["headers"])
    appt_id = await _create_appointment(client, ctx["headers"], patient_id, ctx["doctor_id"])
    invoice_id = await _draft_invoice(client, ctx["headers"], patient_id, appt_id)
    await client.post(
        f"/api/v1/invoices/{invoice_id}/issue",
        headers=ctx["headers"],
    )

    doc2_email = f"doc2-{uuid.uuid4().hex[:8]}@example.com"
    invite = await client.post(
        f"/api/v1/clinics/{clinic_id}/invitations",
        headers=ctx["headers"],
        json={
            "email": doc2_email,
            "role": "doctor",
            "doctor_profile": {
                "specialty": "Pediatrics",
                "prc_license_number": "PRC-456",
                "consultation_fee": "600.00",
            },
        },
    )
    assert invite.status_code == 200
    token = re.search(r"token=([^&]+)", captured["url"]).group(1)
    await client.post(
        f"/api/v1/invitations/{token}/accept",
        json={"full_name": "Doctor Two", "password": "password123"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": doc2_email, "password": "password123"},
    )
    doc2_headers = {
        "Authorization": f"Bearer {login.json()['tokens']['access_token']}",
        "X-Clinic-Id": clinic_id,
    }

    denied = await client.get(
        f"/api/v1/invoices/{invoice_id}",
        headers=doc2_headers,
    )
    assert denied.status_code == 403
