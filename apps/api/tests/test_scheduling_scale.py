import pytest
from httpx import AsyncClient

from tests.test_patients_appointments import _setup_clinic


@pytest.mark.asyncio
async def test_rooms_and_waitlist_and_filters(client: AsyncClient):
    ctx = await _setup_clinic(client)
    headers = ctx["headers"]
    clinic_id = ctx["clinic_id"]

    room = await client.post(
        f"/api/v1/clinics/{clinic_id}/rooms",
        headers=headers,
        json={"name": "Consult 1"},
    )
    assert room.status_code == 200
    room_id = room.json()["id"]
    rooms = await client.get(f"/api/v1/clinics/{clinic_id}/rooms", headers=headers)
    assert any(r["id"] == room_id for r in rooms.json())

    fee = await client.post(
        f"/api/v1/clinics/{clinic_id}/service-fees",
        headers=headers,
        json={"name": "Consult", "amount": "800.00", "duration_minutes": 20},
    )
    assert fee.status_code == 200
    assert fee.json()["duration_minutes"] == 20

    patient = await client.post(
        "/api/v1/patients",
        headers=headers,
        json={"full_name": "Wait Patient", "data_processing_consent": True},
    )
    patient_id = patient.json()["id"]
    wait = await client.post(
        "/api/v1/appointments/waitlist",
        headers=headers,
        json={
            "patient_id": patient_id,
            "doctor_id": ctx["doctor_id"],
            "preferred_date": "2026-12-01",
        },
    )
    assert wait.status_code == 200
    assert wait.json()["patient_name"] == "Wait Patient"
    listed = await client.get("/api/v1/appointments/waitlist", headers=headers)
    assert listed.status_code == 200
    assert listed.json()[0]["status"] == "waiting"

    appt = await client.post(
        "/api/v1/appointments",
        headers=headers,
        json={
            "patient_id": patient_id,
            "doctor_id": ctx["doctor_id"],
            "room_id": room_id,
            "service_fee_id": fee.json()["id"],
            "scheduled_start": "2026-12-01T10:00:00+08:00",
            "scheduled_end": "2026-12-01T10:20:00+08:00",
        },
    )
    assert appt.status_code == 200
    assert appt.json()["room_name"] == "Consult 1"
    assert appt.json()["doctor_name"]
    assert appt.json()["doctor_name"] != ctx["doctor_id"]

    filtered = await client.get(
        "/api/v1/appointments",
        headers=headers,
        params={"q": "Wait", "status": "Scheduled", "doctor_id": ctx["doctor_id"]},
    )
    assert filtered.status_code == 200
    assert any(row["id"] == appt.json()["id"] for row in filtered.json()["items"])

    doctors = await client.get(f"/api/v1/clinics/{clinic_id}/doctors", headers=headers)
    assert doctors.status_code == 200
    assert doctors.json()[0]["full_name"]


@pytest.mark.asyncio
async def test_public_booking_lands_in_scheduled_queue(client: AsyncClient):
    ctx = await _setup_clinic(client)
    clinic = await client.get(f"/api/v1/clinics/{ctx['clinic_id']}", headers=ctx["headers"])
    slug = clinic.json()["slug"]
    off = await client.patch(
        f"/api/v1/clinics/{ctx['clinic_id']}",
        headers=ctx["headers"],
        json={"public_booking_auto_confirm": False},
    )
    assert off.status_code == 200
    assert off.json()["public_booking_auto_confirm"] is False
    req = await client.post(
        f"/api/v1/public/clinics/{slug}/appointment-requests",
        json={
            "full_name": "Public Guest",
            "contact_number": "09170009999",
            "doctor_id": ctx["doctor_id"],
            "scheduled_start": "2026-12-03T11:00:00+08:00",
            "scheduled_end": "2026-12-03T11:30:00+08:00",
        },
    )
    assert req.status_code == 200
    assert req.json()["appointment_status"] == "Scheduled"
    queue = await client.get(
        "/api/v1/appointments",
        headers=ctx["headers"],
        params={"booking_source": "public_link", "status": "Scheduled"},
    )
    assert any(row["id"] == req.json()["id"] for row in queue.json()["items"])
    confirmed = await client.patch(
        f"/api/v1/appointments/{req.json()['id']}",
        headers=ctx["headers"],
        json={"appointment_status": "Confirmed"},
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["appointment_status"] == "Confirmed"
