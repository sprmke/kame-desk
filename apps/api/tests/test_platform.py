import pytest
from httpx import AsyncClient

from app.core.config import settings
from tests.test_patients_appointments import _setup_clinic


def _admin_headers(ctx: dict) -> dict:
    return ctx["headers"]


@pytest.mark.asyncio
async def test_platform_admin_can_list_and_suspend(client: AsyncClient, monkeypatch):
    ctx = await _setup_clinic(client)
    me = await client.get("/api/v1/auth/me", headers=ctx["headers"])
    assert me.status_code == 200
    email = me.json()["email"]
    monkeypatch.setattr(settings, "platform_admin_emails", email)

    me2 = await client.get("/api/v1/auth/me", headers=ctx["headers"])
    assert me2.json()["is_platform_admin"] is True

    org_id = ctx["organization_id"]
    tenants = await client.get("/api/v1/platform/tenants", headers=ctx["headers"])
    assert tenants.status_code == 200
    assert any(row["id"] == org_id for row in tenants.json())

    patched = await client.patch(
        f"/api/v1/platform/tenants/{org_id}",
        headers=ctx["headers"],
        json={"status": "suspended", "plan_key": "pro"},
    )
    assert patched.status_code == 200
    assert patched.json()["status"] == "suspended"
    assert patched.json()["plan_key"] == "pro"

    blocked = await client.get("/api/v1/patients", headers=ctx["headers"])
    assert blocked.status_code == 403
    assert blocked.json()["detail"] == "Organization is suspended"


@pytest.mark.asyncio
async def test_non_admin_cannot_use_platform(client: AsyncClient, monkeypatch):
    ctx = await _setup_clinic(client)
    monkeypatch.setattr(settings, "platform_admin_emails", "")
    res = await client.get("/api/v1/platform/tenants", headers=ctx["headers"])
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_impersonate_returns_owner_token(client: AsyncClient, monkeypatch):
    ctx = await _setup_clinic(client)
    me = await client.get("/api/v1/auth/me", headers=ctx["headers"])
    monkeypatch.setattr(settings, "platform_admin_emails", me.json()["email"])
    org_id = ctx["organization_id"]
    res = await client.post(
        f"/api/v1/platform/tenants/{org_id}/impersonate",
        headers=ctx["headers"],
    )
    assert res.status_code == 200
    token = res.json()["access_token"]
    support = await client.get(
        "/api/v1/patients",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Clinic-Id": ctx["clinic_id"],
        },
    )
    assert support.status_code == 200
    audit = await client.get("/api/v1/platform/audit", headers=ctx["headers"])
    assert audit.status_code == 200
    assert any(row["action"] == "org.impersonated" for row in audit.json())


@pytest.mark.asyncio
async def test_platform_flag_overrides_env_kill_switch(client: AsyncClient, monkeypatch):
    ctx = await _setup_clinic(client)
    me = await client.get("/api/v1/auth/me", headers=ctx["headers"])
    monkeypatch.setattr(settings, "platform_admin_emails", me.json()["email"])
    monkeypatch.setattr(settings, "platform_ai_assistant_enabled", True)
    await client.patch(
        f"/api/v1/clinics/{ctx['clinic_id']}",
        headers=ctx["headers"],
        json={"ai_assistant_enabled": True},
    )
    flag = await client.patch(
        "/api/v1/platform/flags/ai_assistant",
        headers=ctx["headers"],
        json={"enabled": False},
    )
    assert flag.status_code == 200
    blocked = await client.post("/api/v1/assistant/conversations", headers=ctx["headers"])
    assert blocked.status_code == 503
    await client.patch(
        "/api/v1/platform/flags/ai_assistant",
        headers=ctx["headers"],
        json={"enabled": True},
    )


@pytest.mark.asyncio
async def test_register_accepts_plan_key(client: AsyncClient):
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"plan-owner-{__import__('uuid').uuid4().hex[:8]}@example.com",
            "password": "password123",
            "full_name": "Plan Owner",
            "clinic_name": "Plan Clinic",
            "plan_key": "pro",
        },
    )
    assert res.status_code == 200
    headers = {
        "Authorization": f"Bearer {res.json()['tokens']['access_token']}",
        "X-Clinic-Id": res.json()["clinic_id"],
    }
    clinic = await client.get(f"/api/v1/clinics/{res.json()['clinic_id']}", headers=headers)
    assert clinic.status_code == 200
    assert clinic.json()["plan_key"] == "pro"
    assert clinic.json()["status"] == "active"

    catalog = await client.get("/api/v1/plans")
    assert catalog.status_code == 200
    assert {row["key"] for row in catalog.json()} == {"starter", "pro", "clinic"}


@pytest.mark.asyncio
async def test_platform_metrics_are_counts_only(client: AsyncClient, monkeypatch):
    ctx = await _setup_clinic(client)
    me = await client.get("/api/v1/auth/me", headers=ctx["headers"])
    monkeypatch.setattr(settings, "platform_admin_emails", me.json()["email"])
    res = await client.get("/api/v1/platform/metrics", headers=ctx["headers"])
    assert res.status_code == 200
    body = res.json()
    assert "appointments_total" in body
    assert "ai_requests" in body
    assert "sms_sent" in body
    assert "files_total" in body
    assert "clinics_by_ai_requests" in body
    dumped = str(body)
    assert "contact_number" not in dumped
    assert "clinical_notes" not in dumped
