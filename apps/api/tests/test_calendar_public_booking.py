from datetime import UTC, date, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.test_patients_appointments import _setup_clinic


@pytest.mark.asyncio
async def test_available_slots_respects_booking(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Slot Patient"},
    )
    patient_id = patient.json()["id"]
    on_date = date(2026, 10, 8)  # Thu
    start = datetime(2026, 10, 8, 2, 0, tzinfo=UTC)
    end = start + timedelta(minutes=30)
    await client.post(
        "/api/v1/appointments",
        headers=ctx["headers"],
        json={
            "patient_id": patient_id,
            "doctor_id": ctx["doctor_id"],
            "scheduled_start": start.isoformat(),
            "scheduled_end": end.isoformat(),
        },
    )
    slots = await client.get(
        f"/api/v1/appointments/available-slots?doctor_id={ctx['doctor_id']}&date={on_date.isoformat()}",
        headers=ctx["headers"],
    )
    assert slots.status_code == 200
    bodies = slots.json()["slots"]
    assert all(
        not (s["scheduled_start"] == start.isoformat() and s["scheduled_end"] == end.isoformat())
        for s in bodies
    )


@pytest.mark.asyncio
async def test_reschedule_appointment(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Move Patient"},
    )
    patient_id = patient.json()["id"]
    start = datetime(2026, 10, 9, 2, 0, tzinfo=UTC)
    end = start + timedelta(minutes=30)
    created = await client.post(
        "/api/v1/appointments",
        headers=ctx["headers"],
        json={
            "patient_id": patient_id,
            "doctor_id": ctx["doctor_id"],
            "scheduled_start": start.isoformat(),
            "scheduled_end": end.isoformat(),
        },
    )
    appt_id = created.json()["id"]
    new_start = datetime(2026, 10, 9, 3, 0, tzinfo=UTC)
    new_end = new_start + timedelta(minutes=30)
    moved = await client.patch(
        f"/api/v1/appointments/{appt_id}/reschedule",
        headers=ctx["headers"],
        json={
            "scheduled_start": new_start.isoformat(),
            "scheduled_end": new_end.isoformat(),
        },
    )
    assert moved.status_code == 200
    assert moved.json()["scheduled_start"].startswith("2026-10-09T03:00:00")


@pytest.mark.asyncio
async def test_public_booking_flow(client: AsyncClient):
    ctx = await _setup_clinic(client)
    clinic = await client.get(
        f"/api/v1/clinics/{ctx['clinic_id']}",
        headers=ctx["headers"],
    )
    slug = clinic.json()["slug"]
    profile = await client.get(f"/api/v1/public/clinics/{slug}")
    assert profile.status_code == 200
    assert profile.json()["name"]
    on_date = date(2026, 10, 10)
    slots = await client.get(
        f"/api/v1/public/clinics/{slug}/available-slots?doctor_id={ctx['doctor_id']}&date={on_date.isoformat()}"
    )
    assert slots.status_code == 200
    slot_list = slots.json()["slots"]
    assert len(slot_list) > 0
    slot = slot_list[0]
    booked = await client.post(
        f"/api/v1/public/clinics/{slug}/appointment-requests",
        json={
            "doctor_id": ctx["doctor_id"],
            "full_name": "Public Guest",
            "contact_number": "09170001111",
            "scheduled_start": slot["scheduled_start"],
            "scheduled_end": slot["scheduled_end"],
            "reason_for_visit": "Checkup",
        },
    )
    assert booked.status_code == 200

    staff_list = await client.get("/api/v1/appointments", headers=ctx["headers"])
    names = [a.get("patient_name") for a in staff_list.json()["items"]]
    assert "Public Guest" in names


@pytest.mark.asyncio
async def test_public_staff_booking_race(client: AsyncClient):
    ctx = await _setup_clinic(client)
    clinic = await client.get(
        f"/api/v1/clinics/{ctx['clinic_id']}",
        headers=ctx["headers"],
    )
    slug = clinic.json()["slug"]
    on_date = date(2026, 10, 13)
    slots = await client.get(
        f"/api/v1/public/clinics/{slug}/available-slots?doctor_id={ctx['doctor_id']}&date={on_date.isoformat()}"
    )
    slot = slots.json()["slots"][0]
    patient = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Race Patient"},
    )
    patient_id = patient.json()["id"]
    payload = {
        "patient_id": patient_id,
        "doctor_id": ctx["doctor_id"],
        "scheduled_start": slot["scheduled_start"],
        "scheduled_end": slot["scheduled_end"],
    }
    public_payload = {
        "doctor_id": ctx["doctor_id"],
        "full_name": "Race Guest",
        "contact_number": "09170002222",
        "scheduled_start": slot["scheduled_start"],
        "scheduled_end": slot["scheduled_end"],
    }

    async def staff_book():
        return await client.post("/api/v1/appointments", headers=ctx["headers"], json=payload)

    async def public_book():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            return await ac.post(
                f"/api/v1/public/clinics/{slug}/appointment-requests",
                json=public_payload,
            )

    import asyncio

    results = await asyncio.gather(staff_book(), public_book())
    statuses = [r.status_code for r in results]
    assert 200 in statuses
    assert 409 in statuses
