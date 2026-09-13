import re
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from tests.test_patients_appointments import _setup_clinic


async def _create_appointment(client: AsyncClient, ctx: dict) -> str:
    patient = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "SOAP Patient"},
    )
    patient_id = patient.json()["id"]
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
        },
    )
    return appt.json()["id"]


SOAP_BODY = {
    "subjective": "Cough for 3 days",
    "objective": "Clear lungs",
    "assessment": "URTI",
    "plan": "Rest and fluids",
    "follow_up_date": "2026-11-15",
    "specialty_template_key": "general",
}


@pytest.mark.asyncio
async def test_soap_versioning_append_only(client: AsyncClient):
    ctx = await _setup_clinic(client)
    appt_id = await _create_appointment(client, ctx)

    v1 = await client.post(
        f"/api/v1/appointments/{appt_id}/soap-notes",
        headers=ctx["headers"],
        json=SOAP_BODY,
    )
    assert v1.status_code == 200
    assert v1.json()["version_number"] == 1

    v2_body = {**SOAP_BODY, "plan": "Add antihistamine"}
    v2 = await client.post(
        f"/api/v1/appointments/{appt_id}/soap-notes",
        headers=ctx["headers"],
        json=v2_body,
    )
    assert v2.status_code == 200
    assert v2.json()["version_number"] == 2

    history = await client.get(
        f"/api/v1/appointments/{appt_id}/soap-notes",
        headers=ctx["headers"],
    )
    assert history.status_code == 200
    items = history.json()["items"]
    assert len(items) == 2
    assert items[0]["version_number"] == 2
    assert items[1]["version_number"] == 1
    assert items[1]["plan"] == "Rest and fluids"

    specific = await client.get(
        f"/api/v1/appointments/{appt_id}/soap-notes?version=1",
        headers=ctx["headers"],
    )
    assert specific.status_code == 200
    assert specific.json()["items"][0]["plan"] == "Rest and fluids"


@pytest.mark.asyncio
async def test_soap_client_draft_token_retry_is_idempotent(client: AsyncClient):
    ctx = await _setup_clinic(client)
    appt_id = await _create_appointment(client, ctx)
    token = f"offline-{uuid.uuid4().hex[:16]}"

    first = await client.post(
        f"/api/v1/appointments/{appt_id}/soap-notes",
        headers=ctx["headers"],
        json={**SOAP_BODY, "client_draft_token": token},
    )
    assert first.status_code == 200
    assert first.json()["version_number"] == 1
    note_id = first.json()["id"]

    retry = await client.post(
        f"/api/v1/appointments/{appt_id}/soap-notes",
        headers=ctx["headers"],
        json={**SOAP_BODY, "client_draft_token": token},
    )
    assert retry.status_code == 200
    assert retry.json()["id"] == note_id
    assert retry.json()["version_number"] == 1

    history = await client.get(
        f"/api/v1/appointments/{appt_id}/soap-notes",
        headers=ctx["headers"],
    )
    assert len(history.json()["items"]) == 1

    different_token = await client.post(
        f"/api/v1/appointments/{appt_id}/soap-notes",
        headers=ctx["headers"],
        json={**SOAP_BODY, "client_draft_token": f"offline-{uuid.uuid4().hex[:16]}"},
    )
    assert different_token.status_code == 200
    assert different_token.json()["version_number"] == 2


@pytest.mark.asyncio
async def test_soap_sign_and_pdf(client: AsyncClient):
    pytest.importorskip("reportlab")
    ctx = await _setup_clinic(client)
    appt_id = await _create_appointment(client, ctx)

    created = await client.post(
        f"/api/v1/appointments/{appt_id}/soap-notes",
        headers=ctx["headers"],
        json=SOAP_BODY,
    )
    version = created.json()["version_number"]

    signed = await client.post(
        f"/api/v1/appointments/{appt_id}/soap-notes/{version}/sign",
        headers=ctx["headers"],
    )
    assert signed.status_code == 200
    assert signed.json()["signed_at"] is not None

    pdf = await client.get(
        f"/api/v1/appointments/{appt_id}/soap-notes/{version}/pdf",
        headers=ctx["headers"],
    )
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content[:4] == b"%PDF"


@pytest.mark.asyncio
async def test_soap_versions_are_immutable(client: AsyncClient):
    ctx = await _setup_clinic(client)
    appt_id = await _create_appointment(client, ctx)

    v1 = await client.post(
        f"/api/v1/appointments/{appt_id}/soap-notes",
        headers=ctx["headers"],
        json=SOAP_BODY,
    )
    assert v1.status_code == 200

    v2 = await client.post(
        f"/api/v1/appointments/{appt_id}/soap-notes",
        headers=ctx["headers"],
        json={**SOAP_BODY, "plan": "Updated plan only in v2"},
    )
    assert v2.status_code == 200

    history = await client.get(
        f"/api/v1/appointments/{appt_id}/soap-notes?version=1",
        headers=ctx["headers"],
    )
    assert history.status_code == 200
    assert history.json()["items"][0]["plan"] == "Rest and fluids"

    patch_attempt = await client.patch(
        f"/api/v1/appointments/{appt_id}/soap-notes/1",
        headers=ctx["headers"],
        json={"plan": "Hijacked"},
    )
    assert patch_attempt.status_code in (404, 405)


@pytest.mark.asyncio
async def test_reception_blocked_from_soap_by_default(client: AsyncClient, monkeypatch):
    captured: dict[str, str] = {}

    def fake_send(_email: str, accept_url: str, _clinic: str) -> None:
        captured["url"] = accept_url

    monkeypatch.setattr("app.services.clinic_service.send_invitation_email", fake_send)

    ctx = await _setup_clinic(client)
    appt_id = await _create_appointment(client, ctx)

    inv = await client.post(
        f"/api/v1/clinics/{ctx['clinic_id']}/invitations",
        headers=ctx["headers"],
        json={"email": f"reception-{uuid.uuid4().hex[:8]}@example.com", "role": "reception"},
    )
    assert inv.status_code == 200
    reception_email = inv.json()["email"]
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

    blocked = await client.get(
        f"/api/v1/appointments/{appt_id}/soap-notes",
        headers=reception_headers,
    )
    assert blocked.status_code == 403

    write_blocked = await client.post(
        f"/api/v1/appointments/{appt_id}/soap-notes",
        headers=reception_headers,
        json=SOAP_BODY,
    )
    assert write_blocked.status_code == 403


@pytest.mark.asyncio
async def test_reception_can_read_when_clinic_opts_in(client: AsyncClient, monkeypatch):
    captured: dict[str, str] = {}

    def fake_send(_email: str, accept_url: str, _clinic: str) -> None:
        captured["url"] = accept_url

    monkeypatch.setattr("app.services.clinic_service.send_invitation_email", fake_send)

    ctx = await _setup_clinic(client)
    appt_id = await _create_appointment(client, ctx)
    await client.post(
        f"/api/v1/appointments/{appt_id}/soap-notes",
        headers=ctx["headers"],
        json=SOAP_BODY,
    )

    await client.patch(
        f"/api/v1/clinics/{ctx['clinic_id']}",
        headers=ctx["headers"],
        json={"reception_can_view_soap": True},
    )

    inv = await client.post(
        f"/api/v1/clinics/{ctx['clinic_id']}/invitations",
        headers=ctx["headers"],
        json={"email": f"reception2-{uuid.uuid4().hex[:8]}@example.com", "role": "reception"},
    )
    reception_email = inv.json()["email"]
    token = re.search(r"token=([^&]+)", captured["url"]).group(1)
    await client.post(
        f"/api/v1/invitations/{token}/accept",
        json={"full_name": "Front Desk 2", "password": "password123"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": reception_email, "password": "password123"},
    )
    reception_headers = {
        "Authorization": f"Bearer {login.json()['tokens']['access_token']}",
        "X-Clinic-Id": ctx["clinic_id"],
    }

    allowed = await client.get(
        f"/api/v1/appointments/{appt_id}/soap-notes",
        headers=reception_headers,
    )
    assert allowed.status_code == 200
    assert len(allowed.json()["items"]) == 1


@pytest.mark.asyncio
async def test_specialty_templates_list(client: AsyncClient):
    ctx = await _setup_clinic(client)
    res = await client.get("/api/v1/specialty-templates", headers=ctx["headers"])
    assert res.status_code == 200
    keys = {t["template_key"] for t in res.json()}
    assert {
        "general",
        "dental",
        "pediatric",
        "obgyn",
        "psychiatry",
        "dermatology",
    }.issubset(keys)


@pytest.mark.asyncio
async def test_no_soap_update_route(client: AsyncClient):
    from app.main import app

    all_methods: set[str] = set()
    for path, ops in app.openapi()["paths"].items():
        if "soap-notes" not in path:
            continue
        all_methods.update(ops.keys())
    assert all_methods
    assert "patch" not in all_methods
    assert "put" not in all_methods
    assert "post" in all_methods
    assert "get" in all_methods
