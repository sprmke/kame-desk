import uuid

import pytest
from httpx import AsyncClient

from tests.conftest import register_owner


@pytest.mark.asyncio
async def test_register_creates_organization(client: AsyncClient):
    data = await register_owner(client, suffix=str(uuid.uuid4())[:8])
    assert data.get("organization_id")
    assert data.get("organization_name")

    headers = {
        "Authorization": f"Bearer {data['tokens']['access_token']}",
        "X-Clinic-Id": data["clinic_id"],
    }
    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    body = me.json()
    assert body["organizations"]
    assert any(o["is_owner"] for o in body["organizations"])
    assert body["memberships"][0].get("organization_id")


@pytest.mark.asyncio
async def test_owner_can_create_second_clinic(client: AsyncClient):
    suffix = str(uuid.uuid4())[:8]
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"owner-{suffix}@example.com",
            "password": "password123",
            "full_name": "Dr Owner",
            "clinic_name": f"Pro Clinic {suffix}",
            "plan_key": "pro",
        },
    )
    assert res.status_code == 200
    owner = res.json()
    org_id = owner["organization_id"]
    headers = {
        "Authorization": f"Bearer {owner['tokens']['access_token']}",
        "X-Clinic-Id": owner["clinic_id"],
    }

    res = await client.post(
        f"/api/v1/organizations/{org_id}/clinics",
        headers=headers,
        json={"name": "Branch Two"},
    )
    assert res.status_code == 201
    body = res.json()
    assert body["enrollment_status"] == "pending_enrollment"
    assert body["clinic_name"] == "Branch Two"


@pytest.mark.asyncio
async def test_non_owner_cannot_create_clinic(client: AsyncClient, monkeypatch):
    import re

    captured: dict[str, str] = {}

    def fake_send(_email: str, accept_url: str, _clinic: str) -> None:
        captured["url"] = accept_url

    monkeypatch.setattr("app.services.clinic_service.send_invitation_email", fake_send)

    owner = await register_owner(client, suffix=str(uuid.uuid4())[:8])
    org_id = owner["organization_id"]
    headers = {
        "Authorization": f"Bearer {owner['tokens']['access_token']}",
        "X-Clinic-Id": owner["clinic_id"],
    }
    inv = await client.post(
        f"/api/v1/clinics/{owner['clinic_id']}/invitations",
        headers=headers,
        json={"email": "admin@example.com", "role": "admin"},
    )
    assert inv.status_code == 200
    token = re.search(r"token=([^&]+)", captured["url"]).group(1)
    await client.post(
        f"/api/v1/invitations/{token}/accept",
        json={"full_name": "Admin User", "password": "password123"},
    )

    admin_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "password123"},
    )
    admin = admin_login.json()
    admin_headers = {
        "Authorization": f"Bearer {admin['tokens']['access_token']}",
        "X-Clinic-Id": admin["clinic_id"],
    }
    blocked = await client.post(
        f"/api/v1/organizations/{org_id}/clinics",
        headers=admin_headers,
        json={"name": "Blocked Branch"},
    )
    assert blocked.status_code == 403


@pytest.mark.asyncio
async def test_pending_enrollment_blocks_doctor_invite(client: AsyncClient):
    suffix = str(uuid.uuid4())[:8]
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"owner-{suffix}@example.com",
            "password": "password123",
            "full_name": "Dr Owner",
            "clinic_name": f"Pro Clinic {suffix}",
            "plan_key": "pro",
        },
    )
    assert res.status_code == 200
    owner = res.json()
    org_id = owner["organization_id"]
    headers = {
        "Authorization": f"Bearer {owner['tokens']['access_token']}",
        "X-Clinic-Id": owner["clinic_id"],
    }

    created = await client.post(
        f"/api/v1/organizations/{org_id}/clinics",
        headers=headers,
        json={"name": "Pending Branch"},
    )
    assert created.status_code == 201
    pending_clinic_id = created.json()["clinic_id"]
    pending_headers = {**headers, "X-Clinic-Id": pending_clinic_id}

    invite = await client.post(
        f"/api/v1/clinics/{pending_clinic_id}/invitations",
        headers=pending_headers,
        json={"email": "doctor2@example.com", "role": "doctor"},
    )
    assert invite.status_code == 409


@pytest.mark.asyncio
async def test_platform_admin_activates_enrollment(client: AsyncClient, monkeypatch):
    from app.core.config import settings

    suffix = str(uuid.uuid4())[:8]
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"owner-{suffix}@example.com",
            "password": "password123",
            "full_name": "Dr Owner",
            "clinic_name": f"Pro Clinic {suffix}",
            "plan_key": "pro",
        },
    )
    assert res.status_code == 200
    owner = res.json()
    org_id = owner["organization_id"]
    headers = {
        "Authorization": f"Bearer {owner['tokens']['access_token']}",
        "X-Clinic-Id": owner["clinic_id"],
    }
    me = await client.get("/api/v1/auth/me", headers=headers)
    monkeypatch.setattr(settings, "platform_admin_emails", me.json()["email"])

    created = await client.post(
        f"/api/v1/organizations/{org_id}/clinics",
        headers=headers,
        json={"name": "Activate Me"},
    )
    clinic_id = created.json()["clinic_id"]

    activated = await client.patch(
        f"/api/v1/platform/tenants/{org_id}/enrollments/{clinic_id}",
        headers=headers,
        json={"status": "active"},
    )
    assert activated.status_code == 200
    assert activated.json()["status"] == "active"
