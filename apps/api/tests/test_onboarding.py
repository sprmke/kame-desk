import re
import uuid

import pytest
from httpx import AsyncClient

from tests.conftest import register_owner


@pytest.mark.asyncio
async def test_onboarding_flow(client: AsyncClient):
    data = await register_owner(client, suffix=str(uuid.uuid4())[:8])
    headers = {
        "Authorization": f"Bearer {data['tokens']['access_token']}",
        "X-Clinic-Id": data["clinic_id"],
    }
    clinic_id = data["clinic_id"]

    status = await client.get(f"/api/v1/clinics/{clinic_id}/onboarding-status", headers=headers)
    assert status.status_code == 200
    assert status.json()["all_complete"] is False
    assert status.json()["current_step"] == "clinic"

    await client.patch(
        f"/api/v1/clinics/{clinic_id}",
        headers=headers,
        json={
            "address": "123 Main St",
            "contact_phone": "+639171234567",
            "contact_email": "clinic@example.com",
            "license_info": "LIC-001",
        },
    )
    await client.post(
        f"/api/v1/clinics/{clinic_id}/doctors",
        headers=headers,
        json={
            "specialty": "General Practice",
            "prc_license_number": "PRC-123",
            "consultation_fee": "500.00",
        },
    )
    await client.put(
        f"/api/v1/clinics/{clinic_id}/working-hours",
        headers=headers,
        json={
            "working_hours": {"mon": {"open": "09:00", "close": "17:00", "closed": False}},
            "holiday_dates": [],
        },
    )
    await client.post(
        f"/api/v1/clinics/{clinic_id}/onboarding/skip-invite",
        headers=headers,
    )

    final = await client.get(f"/api/v1/clinics/{clinic_id}/onboarding-status", headers=headers)
    body = final.json()
    assert body["all_complete"] is True
    assert body["current_step"] is None


@pytest.mark.asyncio
async def test_invite_accept(client: AsyncClient, monkeypatch):
    captured: dict[str, str] = {}

    def fake_send(_email: str, accept_url: str, _clinic: str) -> None:
        captured["url"] = accept_url

    monkeypatch.setattr("app.services.clinic_service.send_invitation_email", fake_send)

    owner = await register_owner(client, suffix=str(uuid.uuid4())[:8])
    headers = {
        "Authorization": f"Bearer {owner['tokens']['access_token']}",
        "X-Clinic-Id": owner["clinic_id"],
    }
    inv = await client.post(
        f"/api/v1/clinics/{owner['clinic_id']}/invitations",
        headers=headers,
        json={"email": "reception@example.com", "role": "reception"},
    )
    assert inv.status_code == 200
    match = re.search(r"token=([^&]+)", captured["url"])
    assert match
    token = match.group(1)

    accept = await client.post(
        f"/api/v1/invitations/{token}/accept",
        json={"full_name": "Front Desk", "password": "password123"},
    )
    assert accept.status_code == 204

    members = await client.get(
        f"/api/v1/clinics/{owner['clinic_id']}/members",
        headers=headers,
    )
    emails = [m["email"] for m in members.json()]
    assert "reception@example.com" in emails

    dup = await client.post(
        f"/api/v1/clinics/{owner['clinic_id']}/invitations",
        headers=headers,
        json={"email": "reception@example.com", "role": "reception"},
    )
    assert dup.status_code == 409


@pytest.mark.asyncio
async def test_last_owner_guard(client: AsyncClient):
    owner = await register_owner(client, suffix=str(uuid.uuid4())[:8])
    headers = {
        "Authorization": f"Bearer {owner['tokens']['access_token']}",
        "X-Clinic-Id": owner["clinic_id"],
    }
    members = await client.get(
        f"/api/v1/clinics/{owner['clinic_id']}/members",
        headers=headers,
    )
    owner_membership = members.json()[0]

    demote = await client.patch(
        f"/api/v1/clinics/{owner['clinic_id']}/members/{owner_membership['id']}",
        headers=headers,
        json={"role": "reception"},
    )
    assert demote.status_code == 400

    deactivate = await client.patch(
        f"/api/v1/clinics/{owner['clinic_id']}/members/{owner_membership['id']}",
        headers=headers,
        json={"is_active": False},
    )
    assert deactivate.status_code == 400


@pytest.mark.asyncio
async def test_doctor_invite_accept_does_not_double_count_own_seat(
    client: AsyncClient, monkeypatch
):
    """Accepting a pending doctor invite must not count itself as a second
    reservation against the same seat it already holds — starter plan allows
    exactly 1 doctor seat and this invite is the only one."""
    captured: dict[str, str] = {}

    def fake_send(_email: str, accept_url: str, _clinic: str) -> None:
        captured["url"] = accept_url

    monkeypatch.setattr("app.services.clinic_service.send_invitation_email", fake_send)

    owner = await register_owner(client, suffix=str(uuid.uuid4())[:8])
    headers = {
        "Authorization": f"Bearer {owner['tokens']['access_token']}",
        "X-Clinic-Id": owner["clinic_id"],
    }
    doc_email = f"doc-{uuid.uuid4().hex[:8]}@example.com"
    invite = await client.post(
        f"/api/v1/clinics/{owner['clinic_id']}/invitations",
        headers=headers,
        json={
            "email": doc_email,
            "role": "doctor",
            "doctor_profile": {
                "specialty": "Pediatrics",
                "prc_license_number": "PRC-999",
                "consultation_fee": "600.00",
            },
        },
    )
    assert invite.status_code == 200
    token = re.search(r"token=([^&]+)", captured["url"]).group(1)

    accept = await client.post(
        f"/api/v1/invitations/{token}/accept",
        json={"full_name": "Doctor One", "password": "password123"},
    )
    assert accept.status_code == 204

    login = await client.post(
        "/api/v1/auth/login", json={"email": doc_email, "password": "password123"}
    )
    assert login.status_code == 200
    assert "tokens" in login.json()
