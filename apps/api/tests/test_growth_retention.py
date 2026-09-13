import re
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.db import AsyncSessionLocal
from app.models import ActivityLog
from tests.test_patients_appointments import _setup_clinic


async def _create_patient(client: AsyncClient, headers: dict, **overrides) -> str:
    body = {"full_name": "Growth Patient", "data_processing_consent": True}
    body.update(overrides)
    res = await client.post("/api/v1/patients", headers=headers, json=body)
    assert res.status_code == 200
    return res.json()["id"]


async def _book_appointment(client: AsyncClient, ctx: dict, patient_id: str) -> str:
    start = datetime(2026, 10, 14, 2, 0, tzinfo=UTC)
    end = start + timedelta(minutes=30)
    res = await client.post(
        "/api/v1/appointments",
        headers=ctx["headers"],
        json={
            "patient_id": patient_id,
            "doctor_id": ctx["doctor_id"],
            "scheduled_start": start.isoformat(),
            "scheduled_end": end.isoformat(),
        },
    )
    assert res.status_code == 200
    return res.json()["id"]


async def _complete_visit(client: AsyncClient, ctx: dict, appt_id: str) -> None:
    for status in ("Arrived", "In Consultation", "Completed"):
        res = await client.post(
            f"/api/v1/appointments/{appt_id}/visit-status",
            headers=ctx["headers"],
            json={"visit_status": status},
        )
        assert res.status_code == 200


@pytest.mark.asyncio
async def test_growth_settings_roundtrip_and_rbac(client: AsyncClient):
    ctx = await _setup_clinic(client)

    default = await client.get(
        f"/api/v1/clinics/{ctx['clinic_id']}/growth-settings", headers=ctx["headers"]
    )
    assert default.status_code == 200
    assert default.json()["review_requests_enabled"] is False

    body = {
        "google_review_link": "https://g.page/r/example/review",
        "review_requests_enabled": True,
        "doh_accreditation_number": "DOH-1234",
        "doh_accreditation_valid_until": "2027-01-01",
    }
    put = await client.put(
        f"/api/v1/clinics/{ctx['clinic_id']}/growth-settings",
        headers=ctx["headers"],
        json=body,
    )
    assert put.status_code == 200
    assert put.json() == body

    got = await client.get(
        f"/api/v1/clinics/{ctx['clinic_id']}/growth-settings", headers=ctx["headers"]
    )
    assert got.json() == body

    clinic = await client.get(f"/api/v1/clinics/{ctx['clinic_id']}", headers=ctx["headers"])
    assert clinic.json()["growth_settings"] == body


@pytest.mark.asyncio
async def test_review_request_and_nps_sent_on_visit_completed(client: AsyncClient, monkeypatch):
    captured: list[str] = []

    def fake_send(_to, subject, body, sender_name=None):
        captured.append(body)
        return "smtp-local"

    monkeypatch.setattr("app.services.messaging.email_channel.send_reminder_email", fake_send)

    ctx = await _setup_clinic(client)
    await client.put(
        f"/api/v1/clinics/{ctx['clinic_id']}/growth-settings",
        headers=ctx["headers"],
        json={
            "google_review_link": "https://g.page/r/example/review",
            "review_requests_enabled": True,
        },
    )
    patient_id = await _create_patient(client, ctx["headers"], email="growth@example.com")
    appt_id = await _book_appointment(client, ctx, patient_id)
    await _complete_visit(client, ctx, appt_id)

    assert len(captured) == 2
    assert any("g.page/r/example/review" in b for b in captured)
    nps_body = next(b for b in captured if "/nps/" in b)
    token = re.search(r"/nps/([^\s]+)", nps_body).group(1)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ActivityLog).where(
                ActivityLog.action == "review_request.sent",
                ActivityLog.target_id == appt_id,
            )
        )
        assert result.scalar_one_or_none() is not None

    respond = await client.post(
        f"/api/v1/public/nps/{token}/respond", json={"score": 9, "comment": "Great visit"}
    )
    assert respond.status_code == 200
    assert respond.json()["score"] == 9

    replay = await client.post(f"/api/v1/public/nps/{token}/respond", json={"score": 5})
    assert replay.status_code == 400

    report = await client.get("/api/v1/reports/nps", headers=ctx["headers"])
    assert report.status_code == 200
    series = report.json()["series"]
    assert series
    assert series[0]["sent"] >= 1
    assert series[0]["promoters"] >= 1


@pytest.mark.asyncio
async def test_review_request_not_sent_when_disabled(client: AsyncClient, monkeypatch):
    captured: list[str] = []
    monkeypatch.setattr(
        "app.services.messaging.email_channel.send_reminder_email",
        lambda *a, **kw: captured.append(1) or "smtp-local",
    )
    ctx = await _setup_clinic(client)
    patient_id = await _create_patient(client, ctx["headers"], email="nogrowth@example.com")
    appt_id = await _book_appointment(client, ctx, patient_id)
    await _complete_visit(client, ctx, appt_id)
    assert captured == []


@pytest.mark.asyncio
async def test_membership_plan_lifecycle_and_invoice_waiver(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(
        "app.services.invoice_service.upload_object_bytes", lambda key, body, ct: key
    )
    monkeypatch.setattr("app.services.invoice_pdf.render_invoice_pdf", lambda *a, **kw: b"%PDF-1.4")

    ctx = await _setup_clinic(client)
    plan = await client.post(
        f"/api/v1/clinics/{ctx['clinic_id']}/membership-plans",
        headers=ctx["headers"],
        json={
            "name": "Wellness Plan",
            "price": "999.00",
            "billing_interval": "monthly",
            "included_services": [{"category": "consultation", "count_per_period": 1}],
        },
    )
    assert plan.status_code == 200
    plan_id = plan.json()["id"]

    patient_id = await _create_patient(client, ctx["headers"])
    enroll = await client.post(
        f"/api/v1/patients/{patient_id}/membership",
        headers=ctx["headers"],
        json={"plan_id": plan_id},
    )
    assert enroll.status_code == 200
    membership_id = enroll.json()["id"]
    assert enroll.json()["plan_name"] == "Wellness Plan"

    dup = await client.post(
        f"/api/v1/patients/{patient_id}/membership",
        headers=ctx["headers"],
        json={"plan_id": plan_id},
    )
    assert dup.status_code == 409

    invoice = await client.post(
        f"/api/v1/patients/{patient_id}/invoices",
        headers=ctx["headers"],
        json={
            "line_items": [
                {"description": "Consult", "category": "consultation", "unit_price": "500.00"}
            ]
        },
    )
    assert invoice.status_code == 200
    line_items = invoice.json()["line_items"]
    assert len(line_items) == 2
    assert any(Decimal(li["amount"]) < 0 for li in line_items)
    assert Decimal(invoice.json()["total"]) == Decimal("0.00")

    second_visit = await client.post(
        f"/api/v1/patients/{patient_id}/invoices",
        headers=ctx["headers"],
        json={
            "line_items": [
                {"description": "Consult 2", "category": "consultation", "unit_price": "500.00"}
            ]
        },
    )
    assert len(second_visit.json()["line_items"]) == 1
    assert Decimal(second_visit.json()["total"]) == Decimal("500.00")

    cancel = await client.post(
        f"/api/v1/patients/{patient_id}/membership/{membership_id}/cancel",
        headers=ctx["headers"],
    )
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "cancelled"

    none_active = await client.get(
        f"/api/v1/patients/{patient_id}/membership", headers=ctx["headers"]
    )
    assert none_active.status_code == 200
    assert none_active.json() is None


@pytest.mark.asyncio
async def test_membership_plan_write_requires_owner_admin(client: AsyncClient, monkeypatch):
    captured: dict[str, str] = {}

    def fake_send(_email: str, accept_url: str, _clinic: str) -> None:
        captured["url"] = accept_url

    monkeypatch.setattr("app.services.clinic_service.send_invitation_email", fake_send)

    ctx = await _setup_clinic(client)
    reception_email = f"reception-{uuid.uuid4().hex[:8]}@example.com"
    inv = await client.post(
        f"/api/v1/clinics/{ctx['clinic_id']}/invitations",
        headers=ctx["headers"],
        json={"email": reception_email, "role": "reception"},
    )
    assert inv.status_code == 200
    token = re.search(r"token=([^&]+)", captured["url"]).group(1)
    await client.post(
        f"/api/v1/invitations/{token}/accept",
        json={"full_name": "Front Desk", "password": "password123"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": reception_email, "password": "password123"},
    )
    reception_headers = {
        "Authorization": f"Bearer {login.json()['tokens']['access_token']}",
        "X-Clinic-Id": ctx["clinic_id"],
    }

    res = await client.post(
        f"/api/v1/clinics/{ctx['clinic_id']}/membership-plans",
        headers=reception_headers,
        json={"name": "X", "price": "1.00", "billing_interval": "monthly"},
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_financing_hook_disabled_by_default(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(
        "app.services.invoice_service.upload_object_bytes", lambda key, body, ct: key
    )
    monkeypatch.setattr("app.services.invoice_pdf.render_invoice_pdf", lambda *a, **kw: b"%PDF-1.4")
    ctx = await _setup_clinic(client)
    patient_id = await _create_patient(client, ctx["headers"])
    invoice = await client.post(
        f"/api/v1/patients/{patient_id}/invoices",
        headers=ctx["headers"],
        json={"line_items": [{"description": "Consult", "unit_price": "500.00"}]},
    )
    invoice_id = invoice.json()["id"]
    assert invoice.json()["financing_available"] is False

    issued = await client.post(f"/api/v1/invoices/{invoice_id}/issue", headers=ctx["headers"])
    assert issued.status_code == 200

    send = await client.post(
        f"/api/v1/invoices/{invoice_id}/send-to-financing", headers=ctx["headers"]
    )
    assert send.status_code == 404


@pytest.mark.asyncio
async def test_financing_hook_when_enabled(client: AsyncClient, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.financing_partner_enabled", True)
    monkeypatch.setattr("app.routers.invoices.settings.financing_partner_enabled", True)
    monkeypatch.setattr(
        "app.services.invoice_service.upload_object_bytes", lambda key, body, ct: key
    )
    monkeypatch.setattr("app.services.invoice_pdf.render_invoice_pdf", lambda *a, **kw: b"%PDF-1.4")
    ctx = await _setup_clinic(client)
    patient_id = await _create_patient(client, ctx["headers"])
    invoice = await client.post(
        f"/api/v1/patients/{patient_id}/invoices",
        headers=ctx["headers"],
        json={"line_items": [{"description": "Consult", "unit_price": "500.00"}]},
    )
    invoice_id = invoice.json()["id"]
    issued = await client.post(f"/api/v1/invoices/{invoice_id}/issue", headers=ctx["headers"])
    assert issued.json()["financing_available"] is True

    send = await client.post(
        f"/api/v1/invoices/{invoice_id}/send-to-financing", headers=ctx["headers"]
    )
    assert send.status_code == 200
    assert send.json()["financing_status"] == "requested"

    again = await client.post(
        f"/api/v1/invoices/{invoice_id}/send-to-financing", headers=ctx["headers"]
    )
    assert again.status_code == 400


@pytest.mark.asyncio
async def test_referral_chart_share_link(client: AsyncClient, monkeypatch):
    ctx = await _setup_clinic(client)
    patient_id = await _create_patient(client, ctx["headers"])

    template = await client.post(
        f"/api/v1/clinics/{ctx['clinic_id']}/document-templates",
        headers=ctx["headers"],
        json={
            "template_key": "referral_default",
            "name": "Referral",
            "template_type": "referral_letter",
            "body_template": "Refer {{patient.full_name}}",
        },
    )
    assert template.status_code == 200
    template_id = template.json()["id"]

    doc = await client.post(
        f"/api/v1/patients/{patient_id}/documents",
        headers=ctx["headers"],
        json={"template_id": template_id, "referral_recipient": "Dr. Specialist"},
    )
    assert doc.status_code == 200
    document_id = doc.json()["id"]

    share = await client.post(
        f"/api/v1/documents/{document_id}/chart-share", headers=ctx["headers"]
    )
    assert share.status_code == 200
    token = share.json()["share_url"].rsplit("/", 1)[1]

    public = await client.get(f"/api/v1/public/referral-chart/{token}")
    assert public.status_code == 200
    assert "diagnoses" in public.json()

    bad = await client.get("/api/v1/public/referral-chart/not-a-real-token")
    assert bad.status_code == 404


@pytest.mark.asyncio
async def test_fhir_export_returns_bundle(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient_id = await _create_patient(client, ctx["headers"])
    await _book_appointment(client, ctx, patient_id)

    res = await client.get(f"/api/v1/patients/{patient_id}/fhir-export", headers=ctx["headers"])
    assert res.status_code == 200
    body = res.json()
    assert body["resourceType"] == "Bundle"
    resource_types = {e["resource"]["resourceType"] for e in body["entry"]}
    assert resource_types == {"Patient", "Encounter"}
