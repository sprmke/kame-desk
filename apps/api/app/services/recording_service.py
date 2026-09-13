import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.arq_enqueue import enqueue_transcribe_recording
from app.models import ActivityLog, Clinic, ClinicMembership, ConsultationRecording, User
from app.services.appointment_service import get_appointment
from app.services.clinical_access import assert_soap_write
from app.services.storage_service import create_recording_upload


async def assert_recording_consent(db: AsyncSession, clinic_id: uuid.UUID) -> None:
    result = await db.execute(select(Clinic).where(Clinic.id == clinic_id))
    clinic = result.scalar_one()
    if not clinic.recording_consent_enabled:
        raise HTTPException(
            status_code=403,
            detail="Recording consent not enabled for this clinic",
        )


async def create_recording_upload_url(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    appointment_id: uuid.UUID,
    content_type: str,
    file_size_bytes: int,
    duration_seconds: int | None,
    actor: User,
    membership: ClinicMembership,
) -> tuple[ConsultationRecording, str]:
    await assert_recording_consent(db, clinic_id)
    appt = await get_appointment(db, clinic_id, appointment_id)
    await assert_soap_write(db, membership, appt.doctor_id, actor)

    recording = ConsultationRecording(
        appointment_id=appt.id,
        clinic_id=clinic_id,
        r2_key="",
        duration_seconds=duration_seconds,
        transcription_status="pending",
        created_by_user_id=actor.id,
        created_at=datetime.now(UTC),
    )
    db.add(recording)
    await db.flush()

    try:
        upload_url, object_key = create_recording_upload(
            clinic_id,
            appointment_id,
            recording.id,
            content_type,
            file_size_bytes,
        )
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    recording.r2_key = object_key
    await db.commit()
    await db.refresh(recording)
    return recording, upload_url


async def submit_recording_for_transcription(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    appointment_id: uuid.UUID,
    recording_id: uuid.UUID,
    actor: User,
    membership: ClinicMembership,
) -> ConsultationRecording:
    appt = await get_appointment(db, clinic_id, appointment_id)
    await assert_soap_write(db, membership, appt.doctor_id, actor)

    result = await db.execute(
        select(ConsultationRecording).where(
            ConsultationRecording.id == recording_id,
            ConsultationRecording.appointment_id == appointment_id,
            ConsultationRecording.clinic_id == clinic_id,
        )
    )
    recording = result.scalar_one_or_none()
    if recording is None:
        raise HTTPException(status_code=404, detail="Recording not found")
    if recording.transcription_status not in ("pending", "failed"):
        return recording

    recording.transcription_status = "processing"
    recording.processing_started_at = datetime.now(UTC)
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor.id,
            actor_type="user",
            action="recording.transcription_started",
            target_type="appointment",
            target_id=str(appointment_id),
            summary="Consultation recording submitted for transcription",
            metadata_={"recording_id": str(recording_id)},
        )
    )
    await db.commit()
    await db.refresh(recording)
    await enqueue_transcribe_recording(recording.id)
    return recording


async def list_recordings(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    appointment_id: uuid.UUID,
) -> list[ConsultationRecording]:
    await get_appointment(db, clinic_id, appointment_id)
    result = await db.execute(
        select(ConsultationRecording)
        .where(
            ConsultationRecording.appointment_id == appointment_id,
            ConsultationRecording.clinic_id == clinic_id,
        )
        .order_by(ConsultationRecording.created_at.desc())
    )
    return list(result.scalars().all())
