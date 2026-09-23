from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.test_patients_appointments import _setup_clinic

MANILA = ZoneInfo("Asia/Manila")


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


@pytest.mark.asyncio
async def test_public_clinic_service_duration_and_slots(client: AsyncClient):
    ctx = await _setup_clinic(client)
    fee = await client.post(
        f"/api/v1/clinics/{ctx['clinic_id']}/service-fees",
        headers=ctx["headers"],
        json={"name": "Cleaning", "amount": "800.00", "duration_minutes": 60},
    )
    assert fee.status_code == 200
    clinic = await client.get(
        f"/api/v1/clinics/{ctx['clinic_id']}",
        headers=ctx["headers"],
    )
    slug = clinic.json()["slug"]
    profile = await client.get(f"/api/v1/public/clinics/{slug}")
    assert profile.status_code == 200
    services = profile.json()["services"]
    assert services[0]["id"] == fee.json()["id"]
    assert services[0]["duration_minutes"] == 60
    assert profile.json()["advance_booking_days"] == 90
    assert "email" in profile.json()["public_intake_fields"]

    on_date = date(2026, 10, 8)
    slots = await client.get(
        f"/api/v1/public/clinics/{slug}/available-slots"
        f"?doctor_id={ctx['doctor_id']}&date={on_date.isoformat()}&duration_minutes=60"
    )
    assert slots.status_code == 200
    first = slots.json()["slots"][0]
    start = datetime.fromisoformat(first["scheduled_start"])
    end = datetime.fromisoformat(first["scheduled_end"])
    assert (end - start) == timedelta(minutes=60)


@pytest.mark.asyncio
async def test_slots_skip_breaks_and_apply_buffer(client: AsyncClient):
    ctx = await _setup_clinic(client)
    hours = {
        day: {"open": "09:00", "close": "17:00", "closed": False}
        for day in ("mon", "tue", "wed", "thu", "fri")
    }
    hours["thu"] = {
        "open": "09:00",
        "close": "17:00",
        "closed": False,
        "breaks": [{"start": "12:00", "end": "13:00"}],
    }
    hours["sat"] = {"open": "09:00", "close": "12:00", "closed": False}
    hours["sun"] = {"open": "09:00", "close": "12:00", "closed": True}
    await client.put(
        f"/api/v1/clinics/{ctx['clinic_id']}/working-hours",
        headers=ctx["headers"],
        json={"working_hours": hours, "holiday_dates": []},
    )
    await client.patch(
        f"/api/v1/clinics/{ctx['clinic_id']}",
        headers=ctx["headers"],
        json={"slot_buffer_minutes": 15},
    )

    on_date = date(2026, 10, 8)
    slots = await client.get(
        f"/api/v1/appointments/available-slots?doctor_id={ctx['doctor_id']}&date={on_date.isoformat()}",
        headers=ctx["headers"],
    )
    starts = [s["scheduled_start"] for s in slots.json()["slots"]]
    assert all(
        datetime.fromisoformat(s).astimezone(MANILA).strftime("%H:%M") not in {"12:00", "12:30"}
        for s in starts
    )

    start = datetime(2026, 10, 8, 1, 0, tzinfo=UTC)
    end = start + timedelta(minutes=30)
    patient = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Buffer Patient"},
    )
    await client.post(
        "/api/v1/appointments",
        headers=ctx["headers"],
        json={
            "patient_id": patient.json()["id"],
            "doctor_id": ctx["doctor_id"],
            "scheduled_start": start.isoformat(),
            "scheduled_end": end.isoformat(),
        },
    )
    after = await client.get(
        f"/api/v1/appointments/available-slots?doctor_id={ctx['doctor_id']}&date={on_date.isoformat()}",
        headers=ctx["headers"],
    )
    after_starts = [s["scheduled_start"] for s in after.json()["slots"]]
    assert not any(
        datetime.fromisoformat(s).astimezone(MANILA).strftime("%H:%M") == "09:30"
        for s in after_starts
    )


@pytest.mark.asyncio
async def test_advance_booking_cap_and_public_intake(client: AsyncClient):
    ctx = await _setup_clinic(client)
    clinic = await client.get(
        f"/api/v1/clinics/{ctx['clinic_id']}",
        headers=ctx["headers"],
    )
    slug = clinic.json()["slug"]
    await client.patch(
        f"/api/v1/clinics/{ctx['clinic_id']}",
        headers=ctx["headers"],
        json={
            "advance_booking_days": 7,
            "public_intake_fields": {"email": True, "reason": True},
        },
    )
    far = date(2026, 12, 1)
    empty = await client.get(
        f"/api/v1/public/clinics/{slug}/available-slots"
        f"?doctor_id={ctx['doctor_id']}&date={far.isoformat()}"
    )
    assert empty.status_code == 200
    assert empty.json()["slots"] == []

    on_date = date(2026, 9, 24)
    slots = await client.get(
        f"/api/v1/public/clinics/{slug}/available-slots"
        f"?doctor_id={ctx['doctor_id']}&date={on_date.isoformat()}"
    )
    slot = slots.json()["slots"][0]
    missing = await client.post(
        f"/api/v1/public/clinics/{slug}/appointment-requests",
        json={
            "doctor_id": ctx["doctor_id"],
            "full_name": "Intake Guest",
            "contact_number": "09170003333",
            "scheduled_start": slot["scheduled_start"],
            "scheduled_end": slot["scheduled_end"],
        },
    )
    assert missing.status_code == 400

    booked = await client.post(
        f"/api/v1/public/clinics/{slug}/appointment-requests",
        json={
            "doctor_id": ctx["doctor_id"],
            "full_name": "Intake Guest",
            "contact_number": "09170003333",
            "email": "guest@example.com",
            "reason_for_visit": "Checkup",
            "scheduled_start": slot["scheduled_start"],
            "scheduled_end": slot["scheduled_end"],
        },
    )
    assert booked.status_code == 200
    assert booked.json()["reason_for_visit"] == "Checkup"

    patients = await client.get("/api/v1/patients?q=Intake", headers=ctx["headers"])
    assert patients.status_code == 200
    match = next(p for p in patients.json()["items"] if p["full_name"] == "Intake Guest")
    assert match["email"] == "guest@example.com"
