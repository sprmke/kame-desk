from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from tests.test_patients_appointments import _setup_clinic


@pytest.mark.asyncio
async def test_walk_in_creates_arrived_appointment(client: AsyncClient):
    ctx = await _setup_clinic(client)
    res = await client.post(
        "/api/v1/appointments/walk-in",
        headers=ctx["headers"],
        json={
            "doctor_id": ctx["doctor_id"],
            "new_patient": {"full_name": "Walk-in Patient"},
            "reason_for_visit": "Fever",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["appointment_status"] == "Confirmed"
    assert body["current_visit_status"] == "Arrived"


@pytest.mark.asyncio
async def test_mark_no_show_after_end(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "No Show Patient"},
    )
    start = datetime(2020, 1, 1, 2, 0, tzinfo=UTC)
    end = start + timedelta(minutes=30)
    appt = await client.post(
        "/api/v1/appointments",
        headers=ctx["headers"],
        json={
            "patient_id": patient.json()["id"],
            "doctor_id": ctx["doctor_id"],
            "scheduled_start": start.isoformat(),
            "scheduled_end": end.isoformat(),
        },
    )
    appt_id = appt.json()["id"]
    res = await client.post(
        f"/api/v1/appointments/{appt_id}/mark-no-show",
        headers=ctx["headers"],
    )
    assert res.status_code == 200
    assert res.json()["appointment_status"] == "No Show"


@pytest.mark.asyncio
async def test_recurring_series_expansion(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Recurring Patient"},
    )
    start = datetime(2026, 11, 3, 2, 0, tzinfo=UTC)
    res = await client.post(
        "/api/v1/appointment-series",
        headers=ctx["headers"],
        json={
            "patient_id": patient.json()["id"],
            "doctor_id": ctx["doctor_id"],
            "rrule_string": "FREQ=WEEKLY;COUNT=4",
            "series_start": start.isoformat(),
            "duration_minutes": 30,
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["expansion"]["created"] >= 1
    assert "series" in body


@pytest.mark.asyncio
async def test_expand_recurring_idempotent(client: AsyncClient):
    from app.core.db import AsyncSessionLocal
    from app.services.recurring_service import expand_recurring_series

    ctx = await _setup_clinic(client)
    patient = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Idempotent Series"},
    )
    start = datetime(2026, 12, 1, 2, 0, tzinfo=UTC)
    created = await client.post(
        "/api/v1/appointment-series",
        headers=ctx["headers"],
        json={
            "patient_id": patient.json()["id"],
            "doctor_id": ctx["doctor_id"],
            "rrule_string": "FREQ=WEEKLY;COUNT=3",
            "series_start": start.isoformat(),
            "duration_minutes": 30,
        },
    )
    series_id = created.json()["series"]["id"]
    async with AsyncSessionLocal() as db:
        again = await expand_recurring_series(db, series_id)
    assert again["created"] == 0


@pytest.mark.asyncio
async def test_cancel_series_scope_all(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Scope All Patient"},
    )
    start = datetime(2027, 1, 5, 2, 0, tzinfo=UTC)
    series = await client.post(
        "/api/v1/appointment-series",
        headers=ctx["headers"],
        json={
            "patient_id": patient.json()["id"],
            "doctor_id": ctx["doctor_id"],
            "rrule_string": "FREQ=WEEKLY;COUNT=3",
            "series_start": start.isoformat(),
            "duration_minutes": 30,
        },
    )
    assert series.status_code == 200
    listed = await client.get(
        "/api/v1/appointments",
        headers=ctx["headers"],
        params={"patient_id": patient.json()["id"]},
    )
    first_id = listed.json()["items"][0]["id"]
    cancelled = await client.delete(
        f"/api/v1/appointments/{first_id}?scope=all",
        headers=ctx["headers"],
    )
    assert cancelled.status_code == 200
    after = await client.get("/api/v1/appointments", headers=ctx["headers"])
    active = [
        a
        for a in after.json()["items"]
        if a["appointment_status"] not in ("Cancelled", "No Show", "Rescheduled")
    ]
    assert len(active) == 0


@pytest.mark.asyncio
async def test_recurring_conflict_surfaces(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Conflict Patient"},
    )
    start = datetime(2027, 2, 2, 2, 0, tzinfo=UTC)
    end = start + timedelta(minutes=30)
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
    res = await client.post(
        "/api/v1/appointment-series",
        headers=ctx["headers"],
        json={
            "patient_id": patient.json()["id"],
            "doctor_id": ctx["doctor_id"],
            "rrule_string": "FREQ=WEEKLY;COUNT=2",
            "series_start": start.isoformat(),
            "duration_minutes": 30,
        },
    )
    assert res.status_code == 200
    conflicts = res.json()["expansion"]["conflicts"]
    assert len(conflicts) >= 1


@pytest.mark.asyncio
async def test_no_show_increments_patient_count(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Count Patient"},
    )
    patient_id = patient.json()["id"]
    start = datetime(2019, 5, 1, 2, 0, tzinfo=UTC)
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
    await client.post(
        f"/api/v1/appointments/{appt.json()['id']}/mark-no-show",
        headers=ctx["headers"],
    )
    detail = await client.get(f"/api/v1/patients/{patient_id}", headers=ctx["headers"])
    assert detail.json()["no_show_count"] == 1
