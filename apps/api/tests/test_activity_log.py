import re
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select, update

from app.core.db import AsyncSessionLocal
from app.models import ActivityLog
from tests.test_billing import _create_appointment, _create_patient
from tests.test_patients_appointments import _setup_clinic
from tests.test_soap import SOAP_BODY
from tests.test_soap import _create_appointment as _soap_appt


@pytest.mark.asyncio
async def test_activity_log_lists_patient_create(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient_id = await _create_patient(client, ctx["headers"])
    res = await client.get(
        f"/api/v1/clinics/{ctx['clinic_id']}/activity-log",
        headers=ctx["headers"],
        params={"target_type": "patient", "target_id": patient_id},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["total"] >= 1
    assert any("patient" in item["action"] for item in body["items"])


@pytest.mark.asyncio
async def test_activity_log_reception_blocked(client: AsyncClient, monkeypatch):
    captured: dict[str, str] = {}

    def fake_send(_email: str, accept_url: str, _clinic: str) -> None:
        captured["url"] = accept_url

    monkeypatch.setattr("app.services.clinic_service.send_invitation_email", fake_send)
    owner_ctx = await _setup_clinic(client)
    invite = await client.post(
        f"/api/v1/clinics/{owner_ctx['clinic_id']}/invitations",
        headers=owner_ctx["headers"],
        json={"email": f"reception-{uuid.uuid4().hex[:8]}@example.com", "role": "reception"},
    )
    token = re.search(r"token=([^&]+)", captured["url"]).group(1)
    reception_email = invite.json()["email"]
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
        "X-Clinic-Id": owner_ctx["clinic_id"],
    }
    blocked = await client.get(
        f"/api/v1/clinics/{owner_ctx['clinic_id']}/activity-log",
        headers=reception_headers,
    )
    assert blocked.status_code == 403


@pytest.mark.asyncio
async def test_soap_activity_metadata_redacted_for_admin(client: AsyncClient, monkeypatch):
    captured: dict[str, str] = {}

    def fake_send(_email: str, accept_url: str, _clinic: str) -> None:
        captured["url"] = accept_url

    monkeypatch.setattr("app.services.clinic_service.send_invitation_email", fake_send)
    owner_ctx = await _setup_clinic(client)
    appt_id = await _soap_appt(client, owner_ctx)
    soap = await client.post(
        f"/api/v1/appointments/{appt_id}/soap-notes",
        headers=owner_ctx["headers"],
        json={**SOAP_BODY, "diagnosis_primary": "Secret diagnosis"},
    )
    assert soap.status_code == 200

    invite = await client.post(
        f"/api/v1/clinics/{owner_ctx['clinic_id']}/invitations",
        headers=owner_ctx["headers"],
        json={"email": f"admin-{uuid.uuid4().hex[:8]}@example.com", "role": "admin"},
    )
    token = re.search(r"token=([^&]+)", captured["url"]).group(1)
    admin_email = invite.json()["email"]
    await client.post(
        f"/api/v1/invitations/{token}/accept",
        json={"full_name": "Clinic Admin", "password": "password123"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": admin_email, "password": "password123"},
    )
    admin_headers = {
        "Authorization": f"Bearer {login.json()['tokens']['access_token']}",
        "X-Clinic-Id": owner_ctx["clinic_id"],
    }
    res = await client.get(
        f"/api/v1/clinics/{owner_ctx['clinic_id']}/activity-log",
        headers=admin_headers,
        params={"action": "soap.version_created"},
    )
    assert res.status_code == 200
    items = res.json()["items"]
    assert items
    assert items[0]["metadata"] is None


@pytest.mark.asyncio
async def test_activity_log_append_only_trigger():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(ActivityLog).limit(1))
        row = result.scalar_one_or_none()
        if row is None:
            pytest.skip("No activity log rows")
        with pytest.raises(Exception, match="append-only"):
            await db.execute(
                update(ActivityLog).where(ActivityLog.id == row.id).values(summary="tamper")
            )
            await db.commit()
        await db.rollback()


@pytest.mark.asyncio
async def test_appointment_update_writes_activity_log(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient_id = await _create_patient(client, ctx["headers"])
    appt_id = await _create_appointment(client, ctx["headers"], patient_id, ctx["doctor_id"])
    before = await client.get(
        f"/api/v1/clinics/{ctx['clinic_id']}/activity-log",
        headers=ctx["headers"],
        params={"target_type": "appointment", "target_id": appt_id},
    )
    count_before = before.json()["total"]
    patch = await client.patch(
        f"/api/v1/appointments/{appt_id}",
        headers=ctx["headers"],
        json={"notes": "Follow-up call"},
    )
    assert patch.status_code == 200
    after = await client.get(
        f"/api/v1/clinics/{ctx['clinic_id']}/activity-log",
        headers=ctx["headers"],
        params={"target_type": "appointment", "target_id": appt_id},
    )
    assert after.json()["total"] > count_before
