import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select, update

from app.core.db import AsyncSessionLocal
from app.models import Reminder
from app.services.recall_service import generate_recalls_from_follow_ups
from app.services.reminder_service import dispatch_due_reminders
from tests.test_patients_appointments import _setup_clinic
from tests.test_soap import SOAP_BODY


async def _patient_with_email(client: AsyncClient, headers: dict) -> str:
    res = await client.post(
        "/api/v1/patients",
        headers=headers,
        json={
            "full_name": "Reminder Patient",
            "email": "patient@example.com",
            "contact_number": "09171234567",
        },
    )
    assert res.status_code == 200
    return res.json()["id"]


async def _book_appointment(
    client: AsyncClient,
    headers: dict,
    patient_id: str,
    doctor_id: str,
    *,
    start: datetime | None = None,
) -> str:
    if start is None:
        start = datetime(2026, 10, 14, 2, 0, tzinfo=UTC)
    end = start + timedelta(minutes=30)
    res = await client.post(
        "/api/v1/appointments",
        headers=headers,
        json={
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "scheduled_start": start.isoformat(),
            "scheduled_end": end.isoformat(),
        },
    )
    assert res.status_code == 200
    return res.json()["id"]


async def _list_reminders(appointment_id: str) -> list[Reminder]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Reminder).where(Reminder.appointment_id == uuid.UUID(appointment_id))
        )
        return list(result.scalars().all())


@pytest.mark.asyncio
async def test_appointment_create_schedules_confirmation_reminder(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient_id = await _patient_with_email(client, ctx["headers"])
    appt_id = await _book_appointment(client, ctx["headers"], patient_id, ctx["doctor_id"])
    reminders = await _list_reminders(appt_id)
    types = {r.reminder_type for r in reminders}
    assert "confirmation" in types
    assert "reminder_24h" in types
    assert all(r.status == "pending" for r in reminders)
    assert all(r.channel == "email" for r in reminders)


@pytest.mark.asyncio
async def test_cancel_cancels_pending_reminders(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient_id = await _patient_with_email(client, ctx["headers"])
    appt_id = await _book_appointment(client, ctx["headers"], patient_id, ctx["doctor_id"])
    cancel = await client.patch(
        f"/api/v1/appointments/{appt_id}",
        headers=ctx["headers"],
        json={"appointment_status": "Cancelled"},
    )
    assert cancel.status_code == 200
    reminders = await _list_reminders(appt_id)
    notice = [r for r in reminders if r.reminder_type == "cancellation_notice"]
    assert not any(
        r.reminder_type in ("confirmation", "reminder_24h", "reminder_2h") and r.status == "pending"
        for r in reminders
    )
    assert len(notice) >= 1


@pytest.mark.asyncio
async def test_reschedule_cancels_stale_reminders(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient_id = await _patient_with_email(client, ctx["headers"])
    appt_id = await _book_appointment(client, ctx["headers"], patient_id, ctx["doctor_id"])
    before = await _list_reminders(appt_id)
    new_start = datetime(2026, 10, 15, 2, 0, tzinfo=UTC)
    new_end = new_start + timedelta(minutes=30)
    res = await client.patch(
        f"/api/v1/appointments/{appt_id}",
        headers=ctx["headers"],
        json={
            "scheduled_start": new_start.isoformat(),
            "scheduled_end": new_end.isoformat(),
        },
    )
    assert res.status_code == 200
    after = await _list_reminders(appt_id)
    cancelled = [r for r in after if r.status == "cancelled"]
    pending = [r for r in after if r.status == "pending"]
    assert len(cancelled) >= len(before)
    assert any(r.reminder_type == "reschedule_notice" for r in pending)
    assert any(
        r.reminder_type in ("confirmation", "reminder_24h") and r.status == "pending"
        for r in pending
    )


@pytest.mark.asyncio
async def test_dispatch_sends_due_reminders(client: AsyncClient, monkeypatch):
    sent: list[str] = []

    def fake_send(to: str, subject: str, body: str, sender: str | None) -> str:
        sent.append(to)
        return "msg-test"

    monkeypatch.setattr("app.services.messaging.email_channel.send_reminder_email", fake_send)

    ctx = await _setup_clinic(client)
    patient_id = await _patient_with_email(client, ctx["headers"])
    appt_id = await _book_appointment(client, ctx["headers"], patient_id, ctx["doctor_id"])

    async with AsyncSessionLocal() as db:
        await db.execute(
            update(Reminder)
            .where(
                Reminder.appointment_id == uuid.UUID(appt_id),
                Reminder.reminder_type == "confirmation",
            )
            .values(scheduled_send_at=datetime.now(UTC) - timedelta(minutes=5))
        )
        await db.commit()

    async with AsyncSessionLocal() as db:
        result = await dispatch_due_reminders(db)
    assert result["sent"] >= 1
    assert "patient@example.com" in sent


@pytest.mark.asyncio
async def test_sms_blocked_without_credentials(client: AsyncClient):
    ctx = await _setup_clinic(client)
    clinic_id = ctx["clinic_id"]
    patch = await client.patch(
        f"/api/v1/clinics/{clinic_id}/notification-preferences",
        headers=ctx["headers"],
        json={"sms_enabled": True},
    )
    assert patch.status_code == 400

    patient_id = await _patient_with_email(client, ctx["headers"])
    appt_id = await _book_appointment(client, ctx["headers"], patient_id, ctx["doctor_id"])
    reminders = await _list_reminders(appt_id)
    assert all(r.channel != "sms" for r in reminders)


@pytest.mark.asyncio
async def test_sms_dispatch_sends_via_twilio(client: AsyncClient, monkeypatch):
    sent: list[str] = []

    async def fake_sms(*, to: str, body: str, creds: dict) -> str:
        sent.append(to)
        assert creds.get("account_sid") == "ACtestsid00000000000000000000000"
        assert "twilio-stub" not in body
        return "SMreal0001"

    monkeypatch.setattr("app.services.messaging.sms_channel.send_twilio_sms", fake_sms)
    monkeypatch.setattr(
        "app.services.messaging.email_channel.send_reminder_email",
        lambda *args, **kwargs: "smtp-local",
    )

    ctx = await _setup_clinic(client)
    clinic_id = ctx["clinic_id"]
    patch = await client.patch(
        f"/api/v1/clinics/{clinic_id}/notification-preferences",
        headers=ctx["headers"],
        json={
            "sms_enabled": True,
            "twilio_account_sid": "ACtestsid00000000000000000000000",
            "twilio_auth_token": "token",
            "twilio_from_number": "+639170000000",
        },
    )
    assert patch.status_code == 200

    patient_id = await _patient_with_email(client, ctx["headers"])
    appt_id = await _book_appointment(client, ctx["headers"], patient_id, ctx["doctor_id"])
    reminders = await _list_reminders(appt_id)
    assert any(r.channel == "sms" for r in reminders)

    async with AsyncSessionLocal() as db:
        await db.execute(
            update(Reminder)
            .where(
                Reminder.appointment_id == uuid.UUID(appt_id),
                Reminder.channel == "sms",
            )
            .values(scheduled_send_at=datetime.now(UTC) - timedelta(minutes=5))
        )
        await db.commit()

    async with AsyncSessionLocal() as db:
        result = await dispatch_due_reminders(db)
    assert result["sent"] >= 1
    assert sent
    after = await _list_reminders(appt_id)
    sms_sent = [r for r in after if r.channel == "sms" and r.status == "sent"]
    assert sms_sent
    assert all(r.provider_message_id != "twilio-stub" for r in sms_sent)


@pytest.mark.asyncio
async def test_whatsapp_blocked_without_credentials(client: AsyncClient):
    ctx = await _setup_clinic(client)
    clinic_id = ctx["clinic_id"]
    patch = await client.patch(
        f"/api/v1/clinics/{clinic_id}/notification-preferences",
        headers=ctx["headers"],
        json={"whatsapp_enabled": True},
    )
    assert patch.status_code == 400

    patient_id = await _patient_with_email(client, ctx["headers"])
    appt_id = await _book_appointment(client, ctx["headers"], patient_id, ctx["doctor_id"])
    reminders = await _list_reminders(appt_id)
    assert all(r.channel != "whatsapp" for r in reminders)


@pytest.mark.asyncio
async def test_whatsapp_dispatch_sends_via_graph_api(client: AsyncClient, monkeypatch):
    sent: list[str] = []
    phone_number_id = f"PHONE_{uuid.uuid4().hex[:12]}"

    async def fake_whatsapp(
        *, to: str, reminder_type: str, body_param: str, reply_token: str, creds: dict
    ) -> str:
        sent.append(to)
        assert creds.get("phone_number_id") == phone_number_id
        assert creds.get("access_token") == "token"
        return "wamid.real0001"

    monkeypatch.setattr(
        "app.services.messaging.whatsapp_channel.send_whatsapp_template", fake_whatsapp
    )
    monkeypatch.setattr(
        "app.services.messaging.email_channel.send_reminder_email",
        lambda *args, **kwargs: "smtp-local",
    )

    ctx = await _setup_clinic(client)
    clinic_id = ctx["clinic_id"]
    patch = await client.patch(
        f"/api/v1/clinics/{clinic_id}/notification-preferences",
        headers=ctx["headers"],
        json={
            "whatsapp_enabled": True,
            "whatsapp_phone_number_id": phone_number_id,
            "whatsapp_access_token": "token",
        },
    )
    assert patch.status_code == 200
    assert patch.json()["whatsapp_configured"] is True

    patient_id = await _patient_with_email(client, ctx["headers"])
    appt_id = await _book_appointment(client, ctx["headers"], patient_id, ctx["doctor_id"])
    reminders = await _list_reminders(appt_id)
    assert any(r.channel == "whatsapp" for r in reminders)

    async with AsyncSessionLocal() as db:
        await db.execute(
            update(Reminder)
            .where(
                Reminder.appointment_id == uuid.UUID(appt_id),
                Reminder.channel == "whatsapp",
            )
            .values(scheduled_send_at=datetime.now(UTC) - timedelta(minutes=5))
        )
        await db.commit()

    async with AsyncSessionLocal() as db:
        result = await dispatch_due_reminders(db)
    assert result["sent"] >= 1
    assert sent
    after = await _list_reminders(appt_id)
    whatsapp_sent = [r for r in after if r.channel == "whatsapp" and r.status == "sent"]
    assert whatsapp_sent
    assert all(r.provider_message_id == "wamid.real0001" for r in whatsapp_sent)


@pytest.mark.asyncio
async def test_recall_generation_idempotent(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Recall Patient"},
    )
    patient_id = patient.json()["id"]
    follow_up_date = datetime.now(UTC).date() + timedelta(days=14)
    start = datetime.now(UTC).replace(hour=3, minute=0, second=0, microsecond=0) + timedelta(days=1)
    while start.weekday() == 6:
        start += timedelta(days=1)
    appt_id = await _book_appointment(
        client, ctx["headers"], patient_id, ctx["doctor_id"], start=start
    )
    follow_up = follow_up_date.isoformat()
    soap = await client.post(
        f"/api/v1/appointments/{appt_id}/soap-notes",
        headers=ctx["headers"],
        json={**SOAP_BODY, "follow_up_date": follow_up},
    )
    assert soap.status_code == 200

    async with AsyncSessionLocal() as db:
        first = await generate_recalls_from_follow_ups(db)
        second = await generate_recalls_from_follow_ups(db)
    assert first >= 1
    assert second == 0

    recalls = await client.get(
        f"/api/v1/clinics/{ctx['clinic_id']}/recalls",
        headers=ctx["headers"],
    )
    assert recalls.status_code == 200
    items = recalls.json()["items"]
    assert len(items) >= 1
    assert items[0]["source"] == "follow_up_date"


@pytest.mark.asyncio
async def test_public_reminder_confirm(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient_id = await _patient_with_email(client, ctx["headers"])
    appt_id = await _book_appointment(client, ctx["headers"], patient_id, ctx["doctor_id"])
    reminders = await _list_reminders(appt_id)
    token = reminders[0].reply_token
    res = await client.post(
        f"/api/v1/public/reminders/{token}/respond",
        json={"action": "confirm"},
    )
    assert res.status_code == 200
    appt = await client.get(
        f"/api/v1/appointments/{appt_id}",
        headers=ctx["headers"],
    )
    assert appt.json()["appointment_status"] == "Confirmed"
