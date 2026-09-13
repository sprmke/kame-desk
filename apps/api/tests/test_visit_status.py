from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from tests.test_patients_appointments import _setup_clinic


@pytest.mark.asyncio
async def test_visit_status_transitions(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Visit Patient"},
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
    appt_id = appt.json()["id"]

    arrived = await client.post(
        f"/api/v1/appointments/{appt_id}/visit-status",
        headers=ctx["headers"],
        json={"visit_status": "Arrived"},
    )
    assert arrived.status_code == 200
    assert arrived.json()["current_visit_status"] == "Arrived"

    again = await client.post(
        f"/api/v1/appointments/{appt_id}/visit-status",
        headers=ctx["headers"],
        json={"visit_status": "Arrived"},
    )
    assert again.status_code == 200

    consult = await client.post(
        f"/api/v1/appointments/{appt_id}/visit-status",
        headers=ctx["headers"],
        json={"visit_status": "In Consultation"},
    )
    assert consult.status_code == 200

    bad = await client.post(
        f"/api/v1/appointments/{appt_id}/visit-status",
        headers=ctx["headers"],
        json={"visit_status": "Arrived"},
    )
    assert bad.status_code == 400


@pytest.mark.asyncio
async def test_waiting_room_lists_today(client: AsyncClient):
    ctx = await _setup_clinic(client)
    res = await client.get("/api/v1/appointments/waiting-room", headers=ctx["headers"])
    assert res.status_code == 200
    assert "items" in res.json()
    assert "date" in res.json()


@pytest.mark.asyncio
async def test_visit_blocked_on_cancelled_appointment(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Cancelled Patient"},
    )
    patient_id = patient.json()["id"]
    start = datetime(2026, 10, 15, 2, 0, tzinfo=UTC)
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
    appt_id = appt.json()["id"]
    await client.patch(
        f"/api/v1/appointments/{appt_id}",
        headers=ctx["headers"],
        json={"appointment_status": "Cancelled"},
    )
    blocked = await client.post(
        f"/api/v1/appointments/{appt_id}/visit-status",
        headers=ctx["headers"],
        json={"visit_status": "Arrived"},
    )
    assert blocked.status_code == 400
