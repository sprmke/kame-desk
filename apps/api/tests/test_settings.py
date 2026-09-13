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
async def test_receipt_numbering_roundtrip(client: AsyncClient):
    owner = await register_owner(client, suffix=str(uuid.uuid4())[:8])
    headers = _headers(owner)
    clinic_id = owner["clinic_id"]
    put = await client.put(
        f"/api/v1/clinics/{clinic_id}/receipt-numbering",
        headers=headers,
        json={"prefix": "OR-", "next_number": 42, "pad_width": 5},
    )
    assert put.status_code == 200
    assert put.json() == {"prefix": "OR-", "next_number": 42, "pad_width": 5}
    clinic = await client.get(f"/api/v1/clinics/{clinic_id}", headers=headers)
    assert clinic.json()["receipt_numbering"]["next_number"] == 42


@pytest.mark.asyncio
async def test_bir_compliance_roundtrip(client: AsyncClient):
    owner = await register_owner(client, suffix=str(uuid.uuid4())[:8])
    headers = _headers(owner)
    clinic_id = owner["clinic_id"]

    default = await client.get(f"/api/v1/clinics/{clinic_id}/bir-compliance", headers=headers)
    assert default.status_code == 200
    assert default.json() == {
        "tin": None,
        "registered_name": None,
        "registered_address": None,
        "vat_registered": False,
        "compliance_mode": "not_yet_accredited",
        "accreditation_number": None,
        "accreditation_valid_until": None,
    }

    put = await client.put(
        f"/api/v1/clinics/{clinic_id}/bir-compliance",
        headers=headers,
        json={
            "tin": "123-456-789-000",
            "registered_name": "Santos Family Clinic",
            "registered_address": "123 Rizal St, Quezon City",
            "vat_registered": True,
            "compliance_mode": "cas",
            "accreditation_number": "CAS-2026-001",
            "accreditation_valid_until": "2027-01-01",
        },
    )
    assert put.status_code == 200
    body = put.json()
    assert body["tin"] == "123-456-789-000"
    assert body["vat_registered"] is True
    assert body["compliance_mode"] == "cas"

    fetched = await client.get(f"/api/v1/clinics/{clinic_id}/bir-compliance", headers=headers)
    assert fetched.json() == body

    clinic = await client.get(f"/api/v1/clinics/{clinic_id}", headers=headers)
    assert clinic.json()["bir_compliance"] == body

    preview = await client.post(
        f"/api/v1/clinics/{clinic_id}/bir-compliance/preview",
        headers=headers,
        json={
            "tin": "999-999-999-000",
            "vat_registered": True,
            "compliance_mode": "not_yet_accredited",
        },
    )
    assert preview.status_code == 200
    assert preview.headers["content-type"] == "application/pdf"
    assert preview.content.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_bir_compliance_requires_owner_admin(client: AsyncClient, monkeypatch):
    captured: dict[str, str] = {}

    def fake_send(_email: str, accept_url: str, _clinic: str) -> None:
        captured["url"] = accept_url

    monkeypatch.setattr("app.services.clinic_service.send_invitation_email", fake_send)

    owner = await register_owner(client, suffix=str(uuid.uuid4())[:8])
    headers = _headers(owner)
    clinic_id = owner["clinic_id"]

    inv = await client.post(
        f"/api/v1/clinics/{clinic_id}/invitations",
        headers=headers,
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
        "X-Clinic-Id": clinic_id,
    }

    denied = await client.get(
        f"/api/v1/clinics/{clinic_id}/bir-compliance", headers=reception_headers
    )
    assert denied.status_code == 403

    denied_put = await client.put(
        f"/api/v1/clinics/{clinic_id}/bir-compliance",
        headers=reception_headers,
        json={"tin": "000", "vat_registered": False, "compliance_mode": "ptu"},
    )
    assert denied_put.status_code == 403


@pytest.mark.asyncio
async def test_service_fee_update_and_delete(client: AsyncClient):
    owner = await register_owner(client, suffix=str(uuid.uuid4())[:8])
    headers = _headers(owner)
    clinic_id = owner["clinic_id"]
    created = await client.post(
        f"/api/v1/clinics/{clinic_id}/service-fees",
        headers=headers,
        json={"name": "Consult", "amount": "800.00", "category": "visit"},
    )
    assert created.status_code == 200
    fee_id = created.json()["id"]
    patched = await client.patch(
        f"/api/v1/clinics/{clinic_id}/service-fees/{fee_id}",
        headers=headers,
        json={"amount": "900.00"},
    )
    assert patched.status_code == 200
    deleted = await client.delete(
        f"/api/v1/clinics/{clinic_id}/service-fees/{fee_id}",
        headers=headers,
    )
    assert deleted.status_code == 204


@pytest.mark.asyncio
async def test_recall_rules_and_soap_toggle(client: AsyncClient):
    owner = await register_owner(client, suffix=str(uuid.uuid4())[:8])
    headers = _headers(owner)
    clinic_id = owner["clinic_id"]
    soap = await client.patch(
        f"/api/v1/clinics/{clinic_id}",
        headers=headers,
        json={"reception_can_view_soap": True},
    )
    assert soap.status_code == 200
    assert soap.json()["reception_can_view_soap"] is True
    prefs = await client.patch(
        f"/api/v1/clinics/{clinic_id}/notification-preferences",
        headers=headers,
        json={"chronic_condition_rules": [{"condition": "Type 2 Diabetes", "interval_months": 3}]},
    )
    assert prefs.status_code == 200
    rules = prefs.json()["preferences"]["chronic_condition_rules"]
    assert rules[0]["condition"] == "Type 2 Diabetes"


@pytest.mark.asyncio
async def test_template_sample_preview(client: AsyncClient):
    owner = await register_owner(client, suffix=str(uuid.uuid4())[:8])
    headers = _headers(owner)
    clinic_id = owner["clinic_id"]
    preview = await client.post(
        f"/api/v1/clinics/{clinic_id}/document-templates/preview",
        headers=headers,
        json={"body_template": "Seen: {{patient.full_name}} at {{clinic.name}}"},
    )
    assert preview.status_code == 200
    assert "Maria Santos" in preview.json()["preview"]
