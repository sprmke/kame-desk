"""ARQ worker — recurring series, reminders, recalls, transcription, embeddings."""

from arq import cron
from arq.connections import RedisSettings

from app.core.config import settings
from app.core.db import AsyncSessionLocal
from app.services.chart_search_service import fail_stale_transcriptions, purge_expired_recordings
from app.services.embedding_service import upsert_soap_note_embedding
from app.services.notification_service import purge_old_notifications
from app.services.recall_service import generate_all_recalls
from app.services.recurring_service import expand_recurring_series
from app.services.reminder_service import dispatch_due_reminders
from app.services.transcription_service import run_transcribe_recording


async def expand_recurring_series_job(ctx, series_id: str) -> dict:
    async with AsyncSessionLocal() as db:
        import uuid

        return await expand_recurring_series(db, uuid.UUID(series_id))


async def dispatch_due_reminders_job(ctx) -> dict:
    async with AsyncSessionLocal() as db:
        return await dispatch_due_reminders(db)


async def generate_recalls_job(ctx) -> dict:
    async with AsyncSessionLocal() as db:
        return await generate_all_recalls(db)


async def transcribe_recording_job(ctx, recording_id: str) -> dict:
    async with AsyncSessionLocal() as db:
        import uuid

        return await run_transcribe_recording(db, uuid.UUID(recording_id))


async def generate_soap_embedding_job(ctx, soap_note_id: str) -> dict:
    async with AsyncSessionLocal() as db:
        import uuid

        ok = await upsert_soap_note_embedding(db, uuid.UUID(soap_note_id))
        return {"ok": ok}


async def purge_expired_recordings_job(ctx) -> dict:
    async with AsyncSessionLocal() as db:
        deleted = await purge_expired_recordings(db)
        return {"deleted": deleted}


async def fail_stale_transcriptions_job(ctx) -> dict:
    async with AsyncSessionLocal() as db:
        failed = await fail_stale_transcriptions(db)
        return {"failed": failed}


async def purge_old_notifications_job(ctx) -> dict:
    async with AsyncSessionLocal() as db:
        deleted = await purge_old_notifications(db)
        return {"deleted": deleted}


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    functions = [
        expand_recurring_series_job,
        dispatch_due_reminders_job,
        generate_recalls_job,
        transcribe_recording_job,
        generate_soap_embedding_job,
        purge_expired_recordings_job,
        fail_stale_transcriptions_job,
        purge_old_notifications_job,
    ]
    cron_jobs = [
        cron(dispatch_due_reminders_job, minute={0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55}),
        cron(generate_recalls_job, hour=6, minute=0),
        cron(purge_expired_recordings_job, hour=3, minute=0),
        cron(fail_stale_transcriptions_job, minute={0, 15, 30, 45}),
        cron(purge_old_notifications_job, hour=4, minute=0),
    ]
