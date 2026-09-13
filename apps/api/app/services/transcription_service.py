import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.transcription import transcribe_recording_object
from app.models import ActivityLog, ConsultationRecording


async def run_transcribe_recording(db: AsyncSession, recording_id: uuid.UUID) -> dict:
    result = await db.execute(
        select(ConsultationRecording).where(ConsultationRecording.id == recording_id)
    )
    recording = result.scalar_one_or_none()
    if recording is None:
        return {"status": "missing"}
    if recording.transcription_status == "done":
        return {"status": "already_done"}

    if recording.transcription_status == "pending":
        recording.transcription_status = "processing"
        recording.processing_started_at = datetime.now(UTC)

    try:
        transcript = await transcribe_recording_object(recording.r2_key)
        recording.transcript_text = transcript
        recording.transcription_status = "done"
        db.add(
            ActivityLog(
                clinic_id=recording.clinic_id,
                actor_user_id=recording.created_by_user_id,
                actor_type="system",
                action="recording.transcription_completed",
                target_type="appointment",
                target_id=str(recording.appointment_id),
                summary="Consultation recording transcribed",
                metadata_={"recording_id": str(recording.id)},
            )
        )
        await db.commit()
        from app.services.notification_service import notify_transcription_ready

        await notify_transcription_ready(
            db,
            clinic_id=recording.clinic_id,
            recording_id=recording.id,
            doctor_user_id=recording.created_by_user_id,
            patient_id=None,
        )
        return {"status": "done", "recording_id": str(recording.id)}
    except Exception:
        recording.transcription_status = "failed"
        await db.commit()
        return {"status": "failed", "recording_id": str(recording.id)}
