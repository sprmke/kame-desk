import re
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from tests.test_patients_appointments import _setup_clinic


async def _create_appointment(client: AsyncClient, ctx: dict) -> tuple[str, str]:
    patient = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Dental Patient"},
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
    return patient_id, appt.json()["id"]


@pytest.mark.asyncio
async def test_tooth_chart_create_and_list_is_append_only(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient_id, appt_id = await _create_appointment(client, ctx)

    first = await client.post(
        f"/api/v1/patients/{patient_id}/tooth-chart",
        headers=ctx["headers"],
        json={
            "appointment_id": appt_id,
            "tooth_number": 16,
            "surface": "occlusal",
            "condition": "caries",
            "status": "existing",
        },
    )
    assert first.status_code == 200
    assert first.json()["condition"] == "caries"

    second = await client.post(
        f"/api/v1/patients/{patient_id}/tooth-chart",
        headers=ctx["headers"],
        json={
            "appointment_id": appt_id,
            "tooth_number": 16,
            "surface": "occlusal",
            "condition": "filled",
            "status": "existing",
        },
    )
    assert second.status_code == 200

    listed = await client.get(
        f"/api/v1/patients/{patient_id}/tooth-chart",
        headers=ctx["headers"],
    )
    assert listed.status_code == 200
    items = listed.json()
    assert len(items) == 2
    conditions = {item["condition"] for item in items}
    assert conditions == {"caries", "filled"}


@pytest.mark.asyncio
async def test_tooth_chart_rejects_invalid_tooth_number(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient_id, appt_id = await _create_appointment(client, ctx)

    resp = await client.post(
        f"/api/v1/patients/{patient_id}/tooth-chart",
        headers=ctx["headers"],
        json={
            "appointment_id": appt_id,
            "tooth_number": 19,
            "condition": "caries",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_tooth_chart_planned_entry_can_be_added_to_invoice(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient_id, appt_id = await _create_appointment(client, ctx)

    entry = await client.post(
        f"/api/v1/patients/{patient_id}/tooth-chart",
        headers=ctx["headers"],
        json={
            "appointment_id": appt_id,
            "tooth_number": 26,
            "condition": "extraction_planned",
            "status": "planned",
        },
    )
    entry_id = entry.json()["id"]

    added = await client.post(
        f"/api/v1/patients/{patient_id}/tooth-chart/{entry_id}/add-to-invoice",
        headers=ctx["headers"],
        json={"description": "Tooth 26 extraction", "amount": "1500.00"},
    )
    assert added.status_code == 200
    body = added.json()
    assert body["entry"]["status"] == "completed"
    assert body["entry"]["invoice_line_item_id"] is not None
    invoice_id = body["invoice_id"]

    invoice = await client.get(f"/api/v1/invoices/{invoice_id}", headers=ctx["headers"])
    assert invoice.status_code == 200
    descriptions = [li["description"] for li in invoice.json()["line_items"]]
    assert "Tooth 26 extraction" in descriptions

    # Cannot add the same (now-completed) entry to an invoice again.
    replay = await client.post(
        f"/api/v1/patients/{patient_id}/tooth-chart/{entry_id}/add-to-invoice",
        headers=ctx["headers"],
        json={"description": "Tooth 26 extraction", "amount": "1500.00"},
    )
    assert replay.status_code == 400


@pytest.mark.asyncio
async def test_tooth_chart_add_to_invoice_reuses_draft_for_same_appointment(
    client: AsyncClient,
):
    ctx = await _setup_clinic(client)
    patient_id, appt_id = await _create_appointment(client, ctx)

    entries = []
    for tooth in (26, 27):
        entry = await client.post(
            f"/api/v1/patients/{patient_id}/tooth-chart",
            headers=ctx["headers"],
            json={
                "appointment_id": appt_id,
                "tooth_number": tooth,
                "condition": "extraction_planned",
                "status": "planned",
            },
        )
        entries.append(entry.json())

    first = await client.post(
        f"/api/v1/patients/{patient_id}/tooth-chart/{entries[0]['id']}/add-to-invoice",
        headers=ctx["headers"],
        json={"description": "Tooth 26 extraction", "amount": "1500.00"},
    )
    invoice_id = first.json()["invoice_id"]

    second = await client.post(
        f"/api/v1/patients/{patient_id}/tooth-chart/{entries[1]['id']}/add-to-invoice",
        headers=ctx["headers"],
        json={"description": "Tooth 27 extraction", "amount": "1500.00"},
    )
    # Same visit, same draft invoice — never a second draft per tooth.
    assert second.json()["invoice_id"] == invoice_id

    invoice = await client.get(f"/api/v1/invoices/{invoice_id}", headers=ctx["headers"])
    descriptions = [li["description"] for li in invoice.json()["line_items"]]
    assert "Tooth 26 extraction" in descriptions
    assert "Tooth 27 extraction" in descriptions


@pytest.mark.asyncio
async def test_tooth_chart_add_to_invoice_without_appointment_never_reuses_unrelated_draft(
    client: AsyncClient,
):
    ctx = await _setup_clinic(client)
    patient_id, _appt_id = await _create_appointment(client, ctx)

    # An unrelated draft invoice already exists for this patient (e.g. from a prior visit).
    stray = await client.post(
        f"/api/v1/patients/{patient_id}/invoices",
        headers=ctx["headers"],
        json={
            "line_items": [
                {"description": "Old visit fee", "category": "consultation", "unit_price": "300.00"}
            ]
        },
    )
    assert stray.status_code == 200
    stray_invoice_id = stray.json()["id"]

    entry = await client.post(
        f"/api/v1/patients/{patient_id}/tooth-chart",
        headers=ctx["headers"],
        json={"tooth_number": 26, "condition": "extraction_planned", "status": "planned"},
    )
    entry_id = entry.json()["id"]

    added = await client.post(
        f"/api/v1/patients/{patient_id}/tooth-chart/{entry_id}/add-to-invoice",
        headers=ctx["headers"],
        json={"description": "Tooth 26 extraction", "amount": "1500.00"},
    )
    assert added.status_code == 200
    # Must never land on the stray draft it has no relationship to.
    assert added.json()["invoice_id"] != stray_invoice_id


@pytest.mark.asyncio
async def test_tooth_chart_entry_reverts_to_planned_when_invoice_line_item_deleted(
    client: AsyncClient,
):
    ctx = await _setup_clinic(client)
    patient_id, appt_id = await _create_appointment(client, ctx)

    entry = await client.post(
        f"/api/v1/patients/{patient_id}/tooth-chart",
        headers=ctx["headers"],
        json={
            "appointment_id": appt_id,
            "tooth_number": 26,
            "condition": "extraction_planned",
            "status": "planned",
        },
    )
    entry_id = entry.json()["id"]

    added = await client.post(
        f"/api/v1/patients/{patient_id}/tooth-chart/{entry_id}/add-to-invoice",
        headers=ctx["headers"],
        json={"description": "Tooth 26 extraction", "amount": "1500.00"},
    )
    body = added.json()
    invoice_id = body["invoice_id"]
    line_item_id = body["entry"]["invoice_line_item_id"]

    deleted = await client.delete(
        f"/api/v1/invoices/{invoice_id}/line-items/{line_item_id}",
        headers=ctx["headers"],
    )
    assert deleted.status_code == 200

    listed = await client.get(
        f"/api/v1/patients/{patient_id}/tooth-chart",
        headers=ctx["headers"],
    )
    reverted = next(e for e in listed.json() if e["id"] == entry_id)
    assert reverted["status"] == "planned"
    assert reverted["invoice_line_item_id"] is None

    # The now-planned entry can be billed again.
    readded = await client.post(
        f"/api/v1/patients/{patient_id}/tooth-chart/{entry_id}/add-to-invoice",
        headers=ctx["headers"],
        json={"description": "Tooth 26 extraction (retry)", "amount": "1500.00"},
    )
    assert readded.status_code == 200


@pytest.mark.asyncio
async def test_tooth_chart_write_requires_doctor_or_owner(client: AsyncClient, monkeypatch):
    ctx = await _setup_clinic(client)
    patient_id, appt_id = await _create_appointment(client, ctx)

    captured: dict[str, str] = {}

    def fake_send(_email: str, accept_url: str, _clinic: str) -> None:
        captured["url"] = accept_url

    monkeypatch.setattr("app.services.clinic_service.send_invitation_email", fake_send)

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

    resp = await client.post(
        f"/api/v1/patients/{patient_id}/tooth-chart",
        headers=reception_headers,
        json={
            "appointment_id": appt_id,
            "tooth_number": 16,
            "condition": "caries",
        },
    )
    assert resp.status_code == 403
