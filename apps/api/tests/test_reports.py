import re
from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient

from tests.test_billing import _create_appointment, _create_patient, _draft_invoice
from tests.test_patients_appointments import _setup_clinic
from tests.test_soap import SOAP_BODY


@pytest.mark.asyncio
async def test_appointment_report_counts(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient_id = await _create_patient(client, ctx["headers"])
    await _create_appointment(client, ctx["headers"], patient_id, ctx["doctor_id"])

    to_d = date(2026, 10, 31)
    from_d = date(2026, 10, 1)
    res = await client.get(
        "/api/v1/reports/appointments",
        headers=ctx["headers"],
        params={"from_date": from_d.isoformat(), "to_date": to_d.isoformat()},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["series"]
    assert body["series"][0]["booked"] >= 1

    by_doctor = await client.get(
        "/api/v1/reports/appointments",
        headers=ctx["headers"],
        params={
            "from_date": from_d.isoformat(),
            "to_date": to_d.isoformat(),
            "group_by": "doctor",
        },
    )
    assert by_doctor.status_code == 200
    row = by_doctor.json()["series"][0]
    assert row.get("doctor_name")
    assert row["doctor_name"] != row.get("doctor_id")


@pytest.mark.asyncio
async def test_revenue_report_includes_totals(client: AsyncClient, monkeypatch):
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
    invoice_id = await _draft_invoice(
        client,
        ctx["headers"],
        patient_id,
        appt_id,
        [
            {
                "description": "Consult",
                "category": "consultation",
                "quantity": "1",
                "unit_price": "500.00",
            }
        ],
    )
    issue = await client.post(
        f"/api/v1/invoices/{invoice_id}/issue",
        headers=ctx["headers"],
    )
    assert issue.status_code == 200
    pay = await client.post(
        f"/api/v1/invoices/{invoice_id}/payments",
        headers=ctx["headers"],
        json={"method": "cash", "amount": "500.00"},
    )
    assert pay.status_code == 200

    res = await client.get(
        "/api/v1/reports/revenue",
        headers=ctx["headers"],
        params={"from_date": "2026-01-01", "to_date": "2026-12-31"},
    )
    assert res.status_code == 200
    assert "totals" in res.json()
    assert Decimal(res.json()["totals"]["month"]) >= Decimal("500.00")


@pytest.mark.asyncio
async def test_top_diagnoses_blocks_admin(client: AsyncClient, monkeypatch):
    captured: dict[str, str] = {}

    def fake_send(_email: str, accept_url: str, _clinic: str) -> None:
        captured["url"] = accept_url

    monkeypatch.setattr("app.services.clinic_service.send_invitation_email", fake_send)
    owner_ctx = await _setup_clinic(client)
    invite = await client.post(
        f"/api/v1/clinics/{owner_ctx['clinic_id']}/invitations",
        headers=owner_ctx["headers"],
        json={"email": "admin-reports@example.com", "role": "admin"},
    )
    assert invite.status_code == 200
    reception_email = invite.json()["email"]
    token = re.search(r"token=([^&]+)", captured["url"]).group(1)
    await client.post(
        f"/api/v1/invitations/{token}/accept",
        json={"full_name": "Admin User", "password": "password123"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": reception_email, "password": "password123"},
    )
    assert login.status_code == 200
    admin_headers = {
        "Authorization": f"Bearer {login.json()['tokens']['access_token']}",
        "X-Clinic-Id": owner_ctx["clinic_id"],
    }

    blocked = await client.get(
        "/api/v1/reports/top-diagnoses",
        headers=admin_headers,
    )
    assert blocked.status_code == 403


@pytest.mark.asyncio
async def test_top_diagnoses_for_owner(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient_id = await _create_patient(client, ctx["headers"])
    appt_id = await _create_appointment(client, ctx["headers"], patient_id, ctx["doctor_id"])
    soap = await client.post(
        f"/api/v1/appointments/{appt_id}/soap-notes",
        headers=ctx["headers"],
        json={**SOAP_BODY, "diagnosis_primary": "URTI"},
    )
    assert soap.status_code == 200
    version = soap.json()["version_number"]
    sign = await client.post(
        f"/api/v1/appointments/{appt_id}/soap-notes/{version}/sign",
        headers=ctx["headers"],
        json={},
    )
    assert sign.status_code == 200

    res = await client.get(
        "/api/v1/reports/top-diagnoses",
        headers=ctx["headers"],
        params={"from_date": "2026-01-01", "to_date": "2026-12-31"},
    )
    assert res.status_code == 200
    diagnoses = [row["diagnosis"] for row in res.json()["series"]]
    assert "URTI" in diagnoses


@pytest.mark.asyncio
async def test_report_csv_export(client: AsyncClient):
    ctx = await _setup_clinic(client)
    res = await client.get(
        "/api/v1/reports/appointments/export.csv",
        headers=ctx["headers"],
        params={"from_date": "2026-01-01", "to_date": "2026-12-31"},
    )
    assert res.status_code == 200
    assert "booked" in res.text or "no_data" in res.text
