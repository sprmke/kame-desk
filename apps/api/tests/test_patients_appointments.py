import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.conftest import register_owner


async def _setup_clinic(client: AsyncClient) -> dict:
    owner = await register_owner(client, suffix=str(uuid.uuid4())[:8])
    headers = {
        "Authorization": f"Bearer {owner['tokens']['access_token']}",
        "X-Clinic-Id": owner["clinic_id"],
    }
    clinic_id = owner["clinic_id"]
    organization_id = owner.get("organization_id")
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
    await client.put(
        f"/api/v1/clinics/{clinic_id}/working-hours",
        headers=headers,
        json={
            "working_hours": {
                "mon": {"open": "09:00", "close": "17:00", "closed": False},
                "tue": {"open": "09:00", "close": "17:00", "closed": False},
                "wed": {"open": "09:00", "close": "17:00", "closed": False},
                "thu": {"open": "09:00", "close": "17:00", "closed": False},
                "fri": {"open": "09:00", "close": "17:00", "closed": False},
                "sat": {"open": "09:00", "close": "12:00", "closed": False},
                "sun": {"open": "09:00", "close": "12:00", "closed": True},
            },
            "holiday_dates": [],
        },
    )
    doctor = await client.post(
        f"/api/v1/clinics/{clinic_id}/doctors",
        headers=headers,
        json={
            "specialty": "General Practice",
            "prc_license_number": "PRC-123",
            "consultation_fee": "500.00",
        },
    )
    return {
        "headers": headers,
        "clinic_id": clinic_id,
        "organization_id": organization_id,
        "doctor_id": doctor.json()["id"],
    }


@pytest.mark.asyncio
async def test_create_patient_and_search(client: AsyncClient):
    ctx = await _setup_clinic(client)
    created = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Maria Santos", "contact_number": "09171234567"},
    )
    assert created.status_code == 200
    patient_id = created.json()["id"]

    search = await client.get(
        "/api/v1/patients?q=Maria",
        headers=ctx["headers"],
    )
    assert search.status_code == 200
    names = [p["full_name"] for p in search.json()["items"]]
    assert "Maria Santos" in names

    med = await client.put(
        f"/api/v1/patients/{patient_id}/medical-info",
        headers=ctx["headers"],
        json={
            "allergies_reviewed": True,
            "allergies": [{"substance": "Penicillin", "reaction": "Rash", "severity": "moderate"}],
            "current_medications": [],
            "chronic_conditions": [],
            "vaccination_history": [],
        },
    )
    assert med.status_code == 200
    assert med.json()["allergies_reviewed"] is True
    assert med.json()["allergies"][0]["substance"] == "Penicillin"


@pytest.mark.asyncio
async def test_appointment_double_booking_blocked(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Juan Dela Cruz"},
    )
    patient_id = patient.json()["id"]

    start = datetime(2026, 10, 6, 2, 0, tzinfo=UTC)  # 10:00 Asia/Manila (Tue)
    end = start + timedelta(minutes=30)
    payload = {
        "patient_id": patient_id,
        "doctor_id": ctx["doctor_id"],
        "scheduled_start": start.isoformat(),
        "scheduled_end": end.isoformat(),
        "reason_for_visit": "Checkup",
    }
    first = await client.post("/api/v1/appointments", headers=ctx["headers"], json=payload)
    assert first.status_code == 200

    second = await client.post("/api/v1/appointments", headers=ctx["headers"], json=payload)
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_concurrent_double_booking(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Ana Reyes"},
    )
    patient_id = patient.json()["id"]
    start = datetime(2026, 10, 7, 3, 0, tzinfo=UTC)  # 11:00 Asia/Manila (Wed)
    end = start + timedelta(minutes=30)
    payload = {
        "patient_id": patient_id,
        "doctor_id": ctx["doctor_id"],
        "scheduled_start": start.isoformat(),
        "scheduled_end": end.isoformat(),
    }

    async def book():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            return await ac.post("/api/v1/appointments", headers=ctx["headers"], json=payload)

    results = await asyncio.gather(book(), book())
    statuses = [r.status_code for r in results]
    assert 200 in statuses
    assert 409 in statuses
