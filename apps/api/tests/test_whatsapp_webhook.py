import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.config import settings
from app.core.db import AsyncSessionLocal
from app.models import Appointment, Reminder
from tests.test_patients_appointments import _setup_clinic
from tests.test_reminders import _book_appointment, _patient_with_email


async def _configure_whatsapp(client: AsyncClient, ctx: dict) -> str:
    phone_number_id = f"PHONE_{uuid.uuid4().hex[:12]}"
    patch = await client.patch(
        f"/api/v1/clinics/{ctx['clinic_id']}/notification-preferences",
        headers=ctx["headers"],
        json={
            "whatsapp_enabled": True,
            "whatsapp_phone_number_id": phone_number_id,
            "whatsapp_access_token": "token",
        },
    )
    assert patch.status_code == 200
    return phone_number_id


@pytest.mark.asyncio
async def test_webhook_verification_handshake(client: AsyncClient):
    ok = await client.get(
        "/api/v1/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": settings.whatsapp_webhook_verify_token,
            "hub.challenge": "echo-me",
        },
    )
    assert ok.status_code == 200
    assert ok.text == "echo-me"

    bad = await client.get(
        "/api/v1/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong",
            "hub.challenge": "echo-me",
        },
    )
    assert bad.status_code == 403


@pytest.mark.asyncio
async def test_webhook_button_reply_confirms_appointment(client: AsyncClient):
    ctx = await _setup_clinic(client)
    phone_number_id = await _configure_whatsapp(client, ctx)
    patient_id = await _patient_with_email(client, ctx["headers"])
    appt_id = await _book_appointment(client, ctx["headers"], patient_id, ctx["doctor_id"])

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Reminder).where(
                Reminder.appointment_id == uuid.UUID(appt_id),
                Reminder.channel == "whatsapp",
            )
        )
        reminder = result.scalars().first()
        assert reminder is not None
        reply_token = reminder.reply_token

    webhook_payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "metadata": {"phone_number_id": phone_number_id},
                            "messages": [
                                {
                                    "from": "639171234567",
                                    "type": "button",
                                    "button": {"payload": reply_token, "text": "Confirm"},
                                }
                            ],
                        }
                    }
                ]
            }
        ]
    }
    resp = await client.post("/api/v1/webhooks/whatsapp", json=webhook_payload)
    assert resp.status_code == 200
    assert resp.json()["status"] == "confirmed"

    async with AsyncSessionLocal() as db:
        appt = await db.get(Appointment, uuid.UUID(appt_id))
        assert appt.appointment_status == "Confirmed"


@pytest.mark.asyncio
async def test_webhook_ignores_unmatched_phone_number_id(client: AsyncClient):
    resp = await client.post(
        "/api/v1/webhooks/whatsapp",
        json={
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "metadata": {"phone_number_id": "NO_SUCH_PHONE"},
                                "messages": [
                                    {
                                        "from": "639171234567",
                                        "type": "button",
                                        "button": {"payload": "bogus-token", "text": "Confirm"},
                                    }
                                ],
                            }
                        }
                    ]
                }
            ]
        },
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ignored"


@pytest.mark.asyncio
async def test_webhook_ignores_status_callback(client: AsyncClient):
    resp = await client.post(
        "/api/v1/webhooks/whatsapp",
        json={
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "metadata": {"phone_number_id": "PHONE_ID_1"},
                                "statuses": [{"id": "wamid.1", "status": "delivered"}],
                            }
                        }
                    ]
                }
            ]
        },
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ignored"
