import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select, update

from app.core.db import AsyncSessionLocal
from app.models import Patient, Reminder
from tests.test_patients_appointments import _setup_clinic
from tests.test_reminders import _book_appointment, _list_reminders, _patient_with_email


@pytest.mark.asyncio
async def test_opt_out_skips_reminder_scheduling(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient_id = await _patient_with_email(client, ctx["headers"])
    patched = await client.patch(
        f"/api/v1/patients/{patient_id}",
        headers=ctx["headers"],
        json={"reminders_opted_out": True},
    )
    assert patched.status_code == 200
    assert patched.json()["reminders_opted_out"] is True
    appt_id = await _book_appointment(client, ctx["headers"], patient_id, ctx["doctor_id"])
    reminders = await _list_reminders(appt_id)
    assert reminders == []


@pytest.mark.asyncio
async def test_high_no_show_risk_shifts_reminder_lead(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient_id = await _patient_with_email(client, ctx["headers"])
    async with AsyncSessionLocal() as db:
        await db.execute(
            update(Patient).where(Patient.id == uuid.UUID(patient_id)).values(no_show_count=2)
        )
        await db.commit()
    start = datetime(2026, 11, 2, 2, 0, tzinfo=UTC)
    appt_id = await _book_appointment(
        client, ctx["headers"], patient_id, ctx["doctor_id"], start=start
    )
    reminders = await _list_reminders(appt_id)
    by_type = {r.reminder_type: r for r in reminders}
    assert "reminder_24h" in by_type
    lead_24 = start - by_type["reminder_24h"].scheduled_send_at
    assert lead_24 == timedelta(hours=36)


@pytest.mark.asyncio
async def test_staff_can_list_and_retry_failed_reminder(client: AsyncClient, monkeypatch):
    ctx = await _setup_clinic(client)
    patient_id = await _patient_with_email(client, ctx["headers"])
    appt_id = await _book_appointment(client, ctx["headers"], patient_id, ctx["doctor_id"])
    listed = await client.get("/api/v1/reminders", headers=ctx["headers"])
    assert listed.status_code == 200
    assert any(row["appointment_id"] == appt_id for row in listed.json())

    searched = await client.get(
        "/api/v1/reminders/search?page=1&page_size=25&sort=scheduled:desc",
        headers=ctx["headers"],
    )
    assert searched.status_code == 200
    assert searched.json()["total"] >= 1
    assert any(row["appointment_id"] == appt_id for row in searched.json()["items"])

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Reminder).where(Reminder.appointment_id == uuid.UUID(appt_id))
        )
        reminder = result.scalars().first()
        assert reminder is not None
        reminder.status = "failed"
        await db.commit()
        reminder_id = str(reminder.id)

    monkeypatch.setattr(
        "app.services.messaging.email_channel.send_reminder_email",
        lambda *args, **kwargs: "msg-test",
    )
    retry = await client.post(
        f"/api/v1/reminders/{reminder_id}/retry",
        headers=ctx["headers"],
    )
    assert retry.status_code == 200
    assert retry.json()["id"] == reminder_id
