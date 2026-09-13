import logging
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.clients import openai_configured, run_text_llm, use_stub_provider
from app.models import (
    ActivityLog,
    Appointment,
    DoctorProfile,
    Patient,
    Prescription,
    SoapNote,
    User,
    VisitSummary,
)
from app.models.base import new_uuid
from app.services.email_service import send_reminder_email

logger = logging.getLogger(__name__)


async def _appointment_for_clinic(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    appointment_id: uuid.UUID,
) -> Appointment:
    appt = await db.get(Appointment, appointment_id)
    if appt is None or appt.clinic_id != clinic_id:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appt


def _assert_doctor_write(membership) -> None:
    if membership.role not in ("doctor", "owner"):
        raise HTTPException(status_code=403, detail="Visit summary not allowed")


async def _build_summary_input(db: AsyncSession, appt: Appointment) -> str:
    soap = await db.execute(
        select(SoapNote)
        .where(SoapNote.appointment_id == appt.id)
        .order_by(SoapNote.version_number.desc())
        .limit(1)
    )
    note = soap.scalar_one_or_none()
    rx = await db.execute(
        select(Prescription)
        .where(
            Prescription.appointment_id == appt.id,
            Prescription.status == "issued",
        )
        .limit(1)
    )
    prescription = rx.scalar_one_or_none()
    parts: list[str] = []
    if note:
        parts.append(
            f"Subjective: {note.subjective or ''}\n"
            f"Assessment: {note.assessment or ''}\n"
            f"Plan: {note.plan or ''}"
        )
    if prescription:
        parts.append(f"Prescription issued: {prescription.id}")
    return "\n".join(parts) or "Visit completed."


def _stub_summary(chart_text: str) -> str:
    excerpt = chart_text.strip()[:240]
    if excerpt:
        return f"Visit notes on file. Please review and edit before sending.\n\n{excerpt}"
    return "Visit completed. Write a short summary for the patient before sending."


async def _generate_summary_text(chart_text: str) -> tuple[str, bool]:
    """Return (text, generation_failed). Never substitute a canned personalized paragraph."""
    if use_stub_provider():
        return _stub_summary(chart_text), False
    if not openai_configured():
        return "", True
    try:
        text = await run_text_llm(
            (
                "Write a short plain-language visit summary for the patient. "
                "Use only the chart text. No diagnoses beyond what is written."
            ),
            chart_text,
        )
        cleaned = text.strip()
        if not cleaned:
            return "", True
        return cleaned, False
    except Exception:
        logger.exception("Visit summary generation failed")
        return "", True


async def generate_visit_summary_draft(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    appointment_id: uuid.UUID,
    actor: User,
    membership,
) -> VisitSummary:
    _assert_doctor_write(membership)
    appt = await _appointment_for_clinic(db, clinic_id, appointment_id)
    if appt.current_visit_status != "Completed":
        raise HTTPException(status_code=400, detail="Visit is not completed")

    existing = await db.execute(
        select(VisitSummary).where(VisitSummary.appointment_id == appointment_id)
    )
    row = existing.scalar_one_or_none()
    if row is not None:
        return row

    chart_text = await _build_summary_input(db, appt)
    generated, failed = await _generate_summary_text(chart_text)

    summary_id = new_uuid()
    row = VisitSummary(
        id=summary_id,
        clinic_id=clinic_id,
        appointment_id=appointment_id,
        generated_text=generated,
        generation_failed=failed,
        status="draft",
        created_at=datetime.now(UTC),
    )
    db.add(row)
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor.id,
            actor_type="user",
            action="visit_summary.generated",
            target_type="appointment",
            target_id=str(appointment_id),
            summary="Visit summary draft generated",
            metadata_={"visit_summary_id": str(summary_id), "generation_failed": failed},
        )
    )
    await db.commit()
    await db.refresh(row)
    return row


async def create_visit_summary_on_completed(
    db: AsyncSession,
    appt: Appointment,
    actor_id: uuid.UUID,
) -> None:
    existing = await db.execute(select(VisitSummary).where(VisitSummary.appointment_id == appt.id))
    if existing.scalar_one_or_none() is not None:
        return
    chart_text = await _build_summary_input(db, appt)
    generated, failed = await _generate_summary_text(chart_text)
    summary_id = new_uuid()
    row = VisitSummary(
        id=summary_id,
        clinic_id=appt.clinic_id,
        appointment_id=appt.id,
        generated_text=generated,
        generation_failed=failed,
        status="draft",
        created_at=datetime.now(UTC),
    )
    db.add(row)
    db.add(
        ActivityLog(
            clinic_id=appt.clinic_id,
            actor_user_id=actor_id,
            actor_type="system",
            action="visit_summary.generated",
            target_type="appointment",
            target_id=str(appt.id),
            summary="Visit summary draft created on completion",
            metadata_={"visit_summary_id": str(summary_id), "generation_failed": failed},
        )
    )
    if failed:
        from app.services.notification_service import notify_visit_summary_failed

        doc = await db.execute(select(DoctorProfile).where(DoctorProfile.id == appt.doctor_id))
        profile = doc.scalar_one_or_none()
        if profile is not None:
            await notify_visit_summary_failed(
                db,
                clinic_id=appt.clinic_id,
                visit_summary_id=summary_id,
                doctor_user_id=profile.user_id,
                appointment_id=appt.id,
            )


async def approve_visit_summary(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    appointment_id: uuid.UUID,
    actor: User,
    membership,
    edited_text: str | None,
) -> VisitSummary:
    _assert_doctor_write(membership)
    appt = await _appointment_for_clinic(db, clinic_id, appointment_id)
    result = await db.execute(
        select(VisitSummary).where(VisitSummary.appointment_id == appointment_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = await generate_visit_summary_draft(db, clinic_id, appointment_id, actor, membership)
    if row.status == "sent":
        raise HTTPException(status_code=400, detail="Visit summary already sent")
    if row.status == "suppressed":
        raise HTTPException(status_code=400, detail="Visit summary was suppressed")

    patient = await db.get(Patient, appt.patient_id)
    if patient is None or not patient.email:
        raise HTTPException(status_code=400, detail="Patient email required to send summary")

    final_text = (edited_text or row.edited_text or row.generated_text).strip()
    if not final_text:
        raise HTTPException(status_code=400, detail="Write a visit summary before sending.")
    send_reminder_email(
        patient.email,
        "Your visit summary",
        final_text,
        None,
    )
    row.edited_text = edited_text or row.edited_text
    row.status = "sent"
    row.reviewed_by_user_id = actor.id
    row.sent_at = datetime.now(UTC)
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor.id,
            actor_type="user",
            action="visit_summary.sent",
            target_type="appointment",
            target_id=str(appointment_id),
            summary="Visit summary approved and sent",
            metadata_={"visit_summary_id": str(row.id)},
        )
    )
    await db.commit()
    await db.refresh(row)
    return row


async def suppress_visit_summary(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    appointment_id: uuid.UUID,
    actor: User,
    membership,
) -> VisitSummary:
    _assert_doctor_write(membership)
    await _appointment_for_clinic(db, clinic_id, appointment_id)
    result = await db.execute(
        select(VisitSummary).where(VisitSummary.appointment_id == appointment_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = VisitSummary(
            clinic_id=clinic_id,
            appointment_id=appointment_id,
            generated_text="",
            status="suppressed",
            reviewed_by_user_id=actor.id,
            created_at=datetime.now(UTC),
        )
        db.add(row)
    else:
        if row.status == "sent":
            raise HTTPException(status_code=400, detail="Visit summary already sent")
        row.status = "suppressed"
        row.reviewed_by_user_id = actor.id
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor.id,
            actor_type="user",
            action="visit_summary.suppressed",
            target_type="appointment",
            target_id=str(appointment_id),
            summary="Visit summary suppressed",
            metadata_={"visit_summary_id": str(row.id)},
        )
    )
    await db.commit()
    await db.refresh(row)
    return row


async def get_visit_summary(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    appointment_id: uuid.UUID,
    membership,
) -> VisitSummary | None:
    _assert_doctor_write(membership)
    await _appointment_for_clinic(db, clinic_id, appointment_id)
    result = await db.execute(
        select(VisitSummary).where(
            VisitSummary.appointment_id == appointment_id,
            VisitSummary.clinic_id == clinic_id,
        )
    )
    return result.scalar_one_or_none()
