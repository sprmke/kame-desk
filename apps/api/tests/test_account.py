import re
import uuid

import pytest
from httpx import AsyncClient

from tests.conftest import register_owner


def _headers(owner: dict) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {owner['tokens']['access_token']}",
        "X-Clinic-Id": owner["clinic_id"],
    }


@pytest.mark.asyncio
async def test_forgot_unknown_email_is_204(client: AsyncClient):
    res = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "nobody@example.com"},
    )
    assert res.status_code == 204


@pytest.mark.asyncio
async def test_password_reset_revokes_sessions(client: AsyncClient, monkeypatch):
    captured: dict[str, str] = {}

    def fake_send(_to: str, _subject: str, body: str) -> None:
        captured["body"] = body

    monkeypatch.setattr("app.services.account_service.send_account_email", fake_send)

    owner = await register_owner(client, suffix=str(uuid.uuid4())[:8])
    forgot = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": owner["email"]},
    )
    assert forgot.status_code == 204
    match = re.search(r"token=([^\s]+)", captured["body"])
    assert match
    token = match.group(1)

    reset = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "password": "newpass123"},
    )
    assert reset.status_code == 204

    old_refresh = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": owner["tokens"]["refresh_token"]},
    )
    assert old_refresh.status_code == 401

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": owner["email"], "password": "newpass123"},
    )
    assert login.status_code == 200


@pytest.mark.asyncio
async def test_sessions_and_logout_everywhere(client: AsyncClient):
    owner = await register_owner(client, suffix=str(uuid.uuid4())[:8])
    headers = _headers(owner)
    sessions = await client.get("/api/v1/auth/sessions", headers=headers)
    assert sessions.status_code == 200
    assert len(sessions.json()) >= 1

    gone = await client.post("/api/v1/auth/logout-everywhere", headers=headers)
    assert gone.status_code == 204

    refresh = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": owner["tokens"]["refresh_token"]},
    )
    assert refresh.status_code == 401


@pytest.mark.asyncio
async def test_me_includes_verified_email_and_ordered_memberships(client: AsyncClient):
    owner = await register_owner(client, suffix=str(uuid.uuid4())[:8])
    me = await client.get("/api/v1/auth/me", headers=_headers(owner))
    assert me.status_code == 200
    body = me.json()
    assert body["email_verified_at"] is not None
    names = [m["clinic_name"] for m in body["memberships"]]
    assert names == sorted(names)


@pytest.mark.asyncio
async def test_export_and_deletion_request(client: AsyncClient):
    owner = await register_owner(client, suffix=str(uuid.uuid4())[:8])
    headers = _headers(owner)
    clinic_id = owner["clinic_id"]

    patients = await client.get(f"/api/v1/clinics/{clinic_id}/export/patients", headers=headers)
    assert patients.status_code == 200
    assert "patient_number" in patients.text

    appts = await client.get(f"/api/v1/clinics/{clinic_id}/export/appointments", headers=headers)
    assert appts.status_code == 200
    assert "scheduled_start" in appts.text

    delete = await client.post(f"/api/v1/clinics/{clinic_id}/deletion-request", headers=headers)
    assert delete.status_code == 200
    assert delete.json()["deletion_requested_at"] is not None


@pytest.mark.asyncio
async def test_resend_invitation_rotates_token(client: AsyncClient, monkeypatch):
    captured: list[str] = []

    def fake_send(_email: str, accept_url: str, _clinic: str) -> None:
        captured.append(accept_url)

    monkeypatch.setattr("app.services.clinic_service.send_invitation_email", fake_send)

    owner = await register_owner(client, suffix=str(uuid.uuid4())[:8])
    headers = _headers(owner)
    inv = await client.post(
        f"/api/v1/clinics/{owner['clinic_id']}/invitations",
        headers=headers,
        json={"email": f"desk-{uuid.uuid4().hex[:8]}@example.com", "role": "reception"},
    )
    assert inv.status_code == 200
    invitation_id = inv.json()["id"]

    resend = await client.post(
        f"/api/v1/clinics/{owner['clinic_id']}/invitations/{invitation_id}/resend",
        headers=headers,
    )
    assert resend.status_code == 200
    assert len(captured) == 2
    first = re.search(r"token=([^&]+)", captured[0])
    second = re.search(r"token=([^&]+)", captured[1])
    assert first and second
    assert first.group(1) != second.group(1)

    stale = await client.post(
        f"/api/v1/invitations/{first.group(1)}/accept",
        json={"full_name": "Front Desk", "password": "password123"},
    )
    assert stale.status_code == 400

    accept = await client.post(
        f"/api/v1/invitations/{second.group(1)}/accept",
        json={"full_name": "Front Desk", "password": "password123"},
    )
    assert accept.status_code == 204
