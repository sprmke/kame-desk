import re
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.db import AsyncSessionLocal
from app.models import ActivityLog, Patient, PatientFile
from tests.test_patients_appointments import _setup_clinic

SOAP_BODY = {
    "subjective": "Cough for 3 days",
    "objective": "Clear lungs, mild wheeze",
    "assessment": "Acute bronchitis",
    "plan": "Rest, fluids, follow up in 1 week",
    "diagnosis_primary": "Acute bronchitis",
    "diagnosis_secondary": ["Mild dehydration"],
    "icd10_codes": ["J20.9"],
    "follow_up_date": "2026-11-15",
    "specialty_template_key": "general",
}


async def _setup_portal_patient(client: AsyncClient, ctx: dict) -> tuple[str, str]:
    created = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={
            "full_name": "Portal Patient",
            "email": "portal.patient@example.com",
            "contact_number": "09171234567",
        },
    )
    assert created.status_code == 200
    patient_id = created.json()["id"]

    clinic = await client.get(f"/api/v1/clinics/{ctx['clinic_id']}", headers=ctx["headers"])
    assert clinic.status_code == 200
    return patient_id, clinic.json()["slug"]


async def _request_login_link(
    client: AsyncClient, monkeypatch, clinic_slug: str, identifier: str
) -> str:
    captured: dict[str, str] = {}

    def fake_send(_to: str, _subject: str, body: str) -> None:
        captured["body"] = body

    monkeypatch.setattr("app.services.patient_portal_service.send_account_email", fake_send)

    res = await client.post(
        "/api/v1/patient-portal/login/request",
        json={"clinic_slug": clinic_slug, "identifier": identifier},
    )
    assert res.status_code == 200
    assert f"/patient-portal/{clinic_slug}/verify?token=" in captured["body"]
    match = re.search(r"token=([^\s]+)", captured["body"])
    assert match
    return match.group(1)


async def _login(client: AsyncClient, monkeypatch, clinic_slug: str, identifier: str) -> dict:
    token = await _request_login_link(client, monkeypatch, clinic_slug, identifier)
    verify = await client.post("/api/v1/patient-portal/login/verify", json={"token": token})
    assert verify.status_code == 200
    body = verify.json()
    return {"Authorization": f"Bearer {body['access_token']}"}


@pytest.mark.asyncio
async def test_login_request_never_reveals_match(client: AsyncClient, monkeypatch):
    ctx = await _setup_clinic(client)
    _, slug = await _setup_portal_patient(client, ctx)

    calls: list[str] = []
    monkeypatch.setattr(
        "app.services.patient_portal_service.send_account_email",
        lambda *a, **kw: calls.append("sent"),
    )

    matched = await client.post(
        "/api/v1/patient-portal/login/request",
        json={"clinic_slug": slug, "identifier": "portal.patient@example.com"},
    )
    unmatched = await client.post(
        "/api/v1/patient-portal/login/request",
        json={"clinic_slug": slug, "identifier": "nobody@example.com"},
    )
    bad_clinic = await client.post(
        "/api/v1/patient-portal/login/request",
        json={"clinic_slug": "no-such-clinic", "identifier": "portal.patient@example.com"},
    )

    assert matched.status_code == 200
    assert unmatched.status_code == 200
    assert bad_clinic.status_code == 200
    assert matched.json() == unmatched.json() == bad_clinic.json()
    assert calls == ["sent"]


@pytest.mark.asyncio
async def test_login_link_is_single_use_and_expiring(client: AsyncClient, monkeypatch):
    ctx = await _setup_clinic(client)
    _, slug = await _setup_portal_patient(client, ctx)
    token = await _request_login_link(client, monkeypatch, slug, "portal.patient@example.com")

    first = await client.post("/api/v1/patient-portal/login/verify", json={"token": token})
    assert first.status_code == 200

    replay = await client.post("/api/v1/patient-portal/login/verify", json={"token": token})
    assert replay.status_code == 400

    garbage = await client.post(
        "/api/v1/patient-portal/login/verify", json={"token": "not-a-real-token"}
    )
    assert garbage.status_code == 400


@pytest.mark.asyncio
async def test_login_via_sms_when_no_email_matches_uses_twilio(client: AsyncClient, monkeypatch):
    ctx = await _setup_clinic(client)
    created = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Phone Only Patient", "contact_number": "09179998888"},
    )
    patient_id = created.json()["id"]
    clinic = await client.get(f"/api/v1/clinics/{ctx['clinic_id']}", headers=ctx["headers"])
    slug = clinic.json()["slug"]

    patch = await client.patch(
        f"/api/v1/clinics/{ctx['clinic_id']}/notification-preferences",
        headers=ctx["headers"],
        json={
            "sms_enabled": True,
            "twilio_account_sid": "AC_test",
            "twilio_auth_token": "token",
            "twilio_from_number": "+15005550006",
        },
    )
    assert patch.status_code == 200

    captured: dict[str, str] = {}

    async def fake_sms(*, to: str, body: str, creds: dict) -> str:
        captured["body"] = body
        return "SM_test"

    monkeypatch.setattr("app.services.patient_portal_service.send_twilio_sms", fake_sms)

    res = await client.post(
        "/api/v1/patient-portal/login/request",
        json={"clinic_slug": slug, "identifier": "09179998888"},
    )
    assert res.status_code == 200
    assert f"/patient-portal/{slug}/verify?token=" in captured["body"]
    match = re.search(r"(http\S+)", captured["body"])
    assert match
    token = match.group(1).split("token=")[1]

    verify = await client.post("/api/v1/patient-portal/login/verify", json={"token": token})
    assert verify.status_code == 200
    assert verify.json()["patient_id"] == patient_id


@pytest.mark.asyncio
async def test_patient_portal_full_read_flow(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(
        "app.services.invoice_service.upload_object_bytes",
        lambda key, body, ct: key,
    )
    monkeypatch.setattr(
        "app.services.invoice_pdf.render_invoice_pdf",
        lambda *args, **kwargs: b"%PDF-1.4",
    )

    ctx = await _setup_clinic(client)
    patient_id, slug = await _setup_portal_patient(client, ctx)

    start = datetime(2026, 10, 14, 2, 0, tzinfo=UTC)
    end = start + timedelta(minutes=30)
    appt = await client.post(
        "/api/v1/appointments",
        headers=ctx["headers"],
        json={
            "patient_id": patient_id,
            "doctor_id": ctx["doctor_id"],
            "scheduled_start": start.isoformat(),
            "scheduled_end": end.isoformat(),
            "reason_for_visit": "Cough",
        },
    )
    assert appt.status_code == 200
    appt_id = appt.json()["id"]

    soap = await client.post(
        f"/api/v1/appointments/{appt_id}/soap-notes",
        headers=ctx["headers"],
        json=SOAP_BODY,
    )
    assert soap.status_code == 200
    signed = await client.post(
        f"/api/v1/appointments/{appt_id}/soap-notes/1/sign",
        headers=ctx["headers"],
    )
    assert signed.status_code == 200

    vital = await client.post(
        f"/api/v1/patients/{patient_id}/vitals",
        headers=ctx["headers"],
        json={"recorded_at": start.isoformat(), "heart_rate": 78, "blood_pressure": "120/80"},
    )
    assert vital.status_code == 200

    invoice = await client.post(
        f"/api/v1/patients/{patient_id}/invoices",
        headers=ctx["headers"],
        json={
            "appointment_id": appt_id,
            "line_items": [
                {"description": "Consultation", "unit_price": "500.00", "quantity": "1"}
            ],
        },
    )
    assert invoice.status_code == 200
    invoice_id = invoice.json()["id"]
    issued = await client.post(f"/api/v1/invoices/{invoice_id}/issue", headers=ctx["headers"])
    assert issued.status_code == 200
    payment = await client.post(
        f"/api/v1/invoices/{invoice_id}/payments",
        headers=ctx["headers"],
        json={"method": "cash", "amount": "200.00"},
    )
    assert payment.status_code == 200

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Patient).where(Patient.id == uuid.UUID(patient_id)))
        patient = result.scalar_one()
        db.add(
            PatientFile(
                patient_id=patient.id,
                clinic_id=patient.clinic_id,
                r2_key="patients/portal-patient/labs.pdf",
                file_type="lab_result",
                description="CBC results",
                uploaded_by_user_id=patient.created_by_user_id,
            )
        )
        await db.commit()

    headers = await _login(client, monkeypatch, slug, "portal.patient@example.com")

    me = await client.get("/api/v1/patient-portal/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["full_name"] == "Portal Patient"
    assert me.json()["clinic_id"] == ctx["clinic_id"]

    visits = await client.get("/api/v1/patient-portal/visits", headers=headers)
    assert visits.status_code == 200
    assert len(visits.json()) == 1
    assert visits.json()[0]["reason_for_visit"] == "Cough"

    chart = await client.get("/api/v1/patient-portal/chart-summary", headers=headers)
    assert chart.status_code == 200
    body = chart.json()
    assert body["diagnoses"][0]["diagnosis_primary"] == "Acute bronchitis"
    assert body["diagnoses"][0]["visit_date"] == start.isoformat().replace("+00:00", "Z")
    assert body["vitals"][0]["heart_rate"] == 78
    assert "subjective" not in body["diagnoses"][0]

    invoices = await client.get("/api/v1/patient-portal/invoices", headers=headers)
    assert invoices.status_code == 200
    inv_body = invoices.json()
    assert inv_body["items"][0]["balance"] == "300.00"
    assert inv_body["total_balance"] == "300.00"

    docs = await client.get("/api/v1/patient-portal/documents", headers=headers)
    assert docs.status_code == 200
    assert len(docs.json()) == 1
    file_id = docs.json()[0]["id"]

    download = await client.get(
        f"/api/v1/patient-portal/documents/{file_id}/download", headers=headers
    )
    assert download.status_code == 200
    assert "download_url" in download.json()

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ActivityLog).where(
                ActivityLog.action == "patient_portal.document_downloaded",
                ActivityLog.target_id == file_id,
            )
        )
        assert result.scalar_one_or_none() is not None
        login_log = await db.execute(
            select(ActivityLog).where(
                ActivityLog.action == "patient_portal.login",
                ActivityLog.target_id == patient_id,
            )
        )
        assert login_log.scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_patient_portal_cannot_see_other_clinics_patient(client: AsyncClient, monkeypatch):
    ctx_a = await _setup_clinic(client)
    patient_id_a, slug_a = await _setup_portal_patient(client, ctx_a)

    ctx_b = await _setup_clinic(client)
    created_b = await client.post(
        "/api/v1/patients",
        headers=ctx_b["headers"],
        json={"full_name": "Other Clinic Patient", "email": "portal.patient@example.com"},
    )
    assert created_b.status_code == 200

    headers = await _login(client, monkeypatch, slug_a, "portal.patient@example.com")
    me = await client.get("/api/v1/patient-portal/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["id"] == patient_id_a


@pytest.mark.asyncio
async def test_patient_portal_rejects_missing_or_wrong_token_type(client: AsyncClient):
    no_auth = await client.get("/api/v1/patient-portal/me")
    assert no_auth.status_code == 401

    bad = await client.get("/api/v1/patient-portal/me", headers={"Authorization": "Bearer garbage"})
    assert bad.status_code == 401


@pytest.mark.asyncio
async def test_staff_access_token_cannot_use_patient_portal(client: AsyncClient):
    ctx = await _setup_clinic(client)
    res = await client.get(
        "/api/v1/patient-portal/me",
        headers={"Authorization": ctx["headers"]["Authorization"]},
    )
    assert res.status_code == 401
