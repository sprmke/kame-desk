import uuid

from arq import create_pool
from arq.connections import RedisSettings

from app.core.config import settings


async def _enqueue(job_name: str, *args) -> bool:
    try:
        pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
        await pool.enqueue_job(job_name, *args)
        await pool.aclose()
        return True
    except Exception:
        return False


async def enqueue_expand_recurring_series(series_id: uuid.UUID) -> bool:
    return await _enqueue("expand_recurring_series_job", str(series_id))


async def enqueue_transcribe_recording(recording_id: uuid.UUID) -> bool:
    return await _enqueue("transcribe_recording_job", str(recording_id))


async def enqueue_generate_soap_embedding(soap_note_id: uuid.UUID) -> bool:
    return await _enqueue("generate_soap_embedding_job", str(soap_note_id))
