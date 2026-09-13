import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text

from app.models import ConsultationRecording
from app.services.chart_search_service import fail_stale_transcriptions, purge_expired_recordings
from app.services.embedding_service import upsert_soap_note_embedding
from app.services.transcription_service import run_transcribe_recording
from tests.test_patients_appointments import _setup_clinic
from tests.test_soap import SOAP_BODY, _create_appointment


async def _enable_recording_consent(client: AsyncClient, ctx: dict) -> None:
    res = await client.patch(
        f"/api/v1/clinics/{ctx['clinic_id']}",
        headers=ctx["headers"],
        json={"recording_consent_enabled": True},
    )
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_recording_requires_consent(client: AsyncClient):
    ctx = await _setup_clinic(client)
    appt_id = await _create_appointment(client, ctx)

    blocked = await client.post(
        f"/api/v1/appointments/{appt_id}/recordings",
        headers=ctx["headers"],
        json={
            "content_type": "audio/webm",
            "file_size_bytes": 1200,
            "duration_seconds": 5,
        },
    )
    assert blocked.status_code == 403


@pytest.mark.asyncio
async def test_transcription_job_completes(client: AsyncClient):
    ctx = await _setup_clinic(client)
    await _enable_recording_consent(client, ctx)
    appt_id = await _create_appointment(client, ctx)

    with patch(
        "app.services.storage_service.create_recording_upload",
        return_value=("http://upload.test/audio", "clinics/test/recording.webm"),
    ):
        created = await client.post(
            f"/api/v1/appointments/{appt_id}/recordings",
            headers=ctx["headers"],
            json={
                "content_type": "audio/webm",
                "file_size_bytes": 1200,
                "duration_seconds": 5,
            },
        )
    assert created.status_code == 200
    recording_id = created.json()["recording"]["id"]

    submitted = await client.post(
        f"/api/v1/appointments/{appt_id}/recordings/{recording_id}/submit",
        headers=ctx["headers"],
    )
    assert submitted.status_code == 200

    with patch(
        "app.services.transcription_service.transcribe_recording_object",
        new=AsyncMock(return_value="Patient reports headache for three days."),
    ):
        from app.core.db import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            result = await run_transcribe_recording(db, uuid.UUID(recording_id))
            assert result["status"] == "done"

    listed = await client.get(
        f"/api/v1/appointments/{appt_id}/recordings",
        headers=ctx["headers"],
    )
    assert listed.json()[0]["transcription_status"] == "done"
    assert "headache" in listed.json()[0]["transcript_text"]


@pytest.mark.asyncio
async def test_embedding_generated_on_soap_save(client: AsyncClient):
    ctx = await _setup_clinic(client)
    appt_id = await _create_appointment(client, ctx)

    saved = await client.post(
        f"/api/v1/appointments/{appt_id}/soap-notes",
        headers=ctx["headers"],
        json={**SOAP_BODY, "assessment": "Recurring migraine pattern"},
    )
    assert saved.status_code == 200
    soap_note_id = saved.json()["id"]

    from app.core.db import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        ok = await upsert_soap_note_embedding(db, uuid.UUID(soap_note_id))
        assert ok
        count = await db.execute(
            text("SELECT COUNT(*) FROM soap_note_embeddings WHERE soap_note_id = :id"),
            {"id": soap_note_id},
        )
        assert count.scalar_one() == 1


@pytest.mark.asyncio
async def test_chart_search_returns_real_chart_links(client: AsyncClient):
    ctx = await _setup_clinic(client)
    appt_id = await _create_appointment(client, ctx)

    saved = await client.post(
        f"/api/v1/appointments/{appt_id}/soap-notes",
        headers=ctx["headers"],
        json={**SOAP_BODY, "assessment": "Recurring migraine with aura"},
    )
    soap_note_id = saved.json()["id"]

    from app.core.db import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        await upsert_soap_note_embedding(db, uuid.UUID(soap_note_id))

    search = await client.get(
        f"/api/v1/clinics/{ctx['clinic_id']}/chart-search?q=migraine",
        headers=ctx["headers"],
    )
    assert search.status_code == 200
    items = search.json()["items"]
    assert items
    assert items[0]["soap_note_id"] == soap_note_id
    assert items[0]["appointment_id"] == appt_id


@pytest.mark.asyncio
async def test_chart_search_blocks_reception(client: AsyncClient, monkeypatch):
    import re

    captured: dict[str, str] = {}

    def fake_send(_email: str, accept_url: str, _clinic: str) -> None:
        captured["url"] = accept_url

    monkeypatch.setattr("app.services.clinic_service.send_invitation_email", fake_send)

    ctx = await _setup_clinic(client)
    inv = await client.post(
        f"/api/v1/clinics/{ctx['clinic_id']}/invitations",
        headers=ctx["headers"],
        json={"email": f"reception-{uuid.uuid4().hex[:8]}@example.com", "role": "reception"},
    )
    token = re.search(r"token=([^&]+)", captured["url"]).group(1)
    await client.post(
        f"/api/v1/invitations/{token}/accept",
        json={"full_name": "Front Desk", "password": "password123"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": inv.json()["email"], "password": "password123"},
    )
    reception_headers = {
        "Authorization": f"Bearer {login.json()['tokens']['access_token']}",
        "X-Clinic-Id": ctx["clinic_id"],
    }

    blocked = await client.get(
        f"/api/v1/clinics/{ctx['clinic_id']}/chart-search?q=migraine",
        headers=reception_headers,
    )
    assert blocked.status_code == 403


@pytest.mark.asyncio
async def test_fail_stale_transcriptions_marks_failed(client: AsyncClient):
    from app.core.db import AsyncSessionLocal
    from tests.conftest import register_owner

    ctx = await _setup_clinic(client)
    owner = await register_owner(client, suffix=uuid.uuid4().hex[:8])
    appt_id = await _create_appointment(client, ctx)

    async with AsyncSessionLocal() as db:
        row = ConsultationRecording(
            appointment_id=uuid.UUID(appt_id),
            clinic_id=uuid.UUID(ctx["clinic_id"]),
            r2_key="clinics/x.webm",
            transcription_status="processing",
            created_by_user_id=uuid.UUID(owner["user_id"]),
            created_at=datetime.now(UTC),
            processing_started_at=datetime.now(UTC) - timedelta(hours=2),
        )
        db.add(row)
        await db.commit()

        failed = await fail_stale_transcriptions(db)
        assert failed >= 1

        refreshed = await db.execute(
            select(ConsultationRecording).where(ConsultationRecording.id == row.id)
        )
        assert refreshed.scalar_one().transcription_status == "failed"


@pytest.mark.asyncio
async def test_purge_expired_recordings_deletes_old_rows(client: AsyncClient):
    from app.core.db import AsyncSessionLocal
    from tests.conftest import register_owner

    ctx = await _setup_clinic(client)
    owner = await register_owner(client, suffix=uuid.uuid4().hex[:8])
    appt_id = await _create_appointment(client, ctx)

    async with AsyncSessionLocal() as db:
        row = ConsultationRecording(
            appointment_id=uuid.UUID(appt_id),
            clinic_id=uuid.UUID(ctx["clinic_id"]),
            r2_key="clinics/old.webm",
            transcription_status="done",
            created_by_user_id=uuid.UUID(owner["user_id"]),
            created_at=datetime.now(UTC) - timedelta(days=120),
        )
        db.add(row)
        await db.commit()

        with patch("app.services.storage_service.delete_object"):
            deleted = await purge_expired_recordings(db)
            assert deleted >= 1
