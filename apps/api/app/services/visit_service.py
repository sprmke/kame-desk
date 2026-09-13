import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Literal
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.realtime_bus import publish_clinic_event
from app.models import ActivityLog, Appointment, Clinic, Patient, VisitStatusEvent
from app.services.notification_service import notify_visit_status

logger = logging.getLogger(__name__)

TERMINAL_STATUSES = {"Cancelled", "No Show", "Rescheduled"}

MANILA = ZoneInfo("Asia/Manila")
VisitStatus = Literal["Arrived", "In Consultation", "Completed"]

VISIT_TRANSITIONS: dict[str | None, set[str]] = {
    None: {"Arrived"},
    "Arrived": {"In Consultation"},
    "In Consultation": {"Completed"},
    "Completed": set(),
}


def _validate_visit_transition(current: str | None, new: str) -> None:
    allowed = VISIT_TRANSITIONS.get(current, set())
    if new not in allowed:
        if current == new:
            return
        raise HTTPException(status_code=400, detail="Invalid visit status transition")


async def transition_visit_status(
    db: AsyncSession,
    appt: Appointment,
    visit_status: str,
    actor_id: uuid.UUID,
) -> Appointment:
    if appt.appointment_status in TERMINAL_STATUSES:
        raise HTTPException(status_code=400, detail="Appointment is not active")

    current = appt.current_visit_status
    if current == visit_status:
        return appt

    _validate_visit_transition(current, visit_status)

    event = VisitStatusEvent(
        appointment_id=appt.id,
        clinic_id=appt.clinic_id,
        visit_status=visit_status,
        changed_by_user_id=actor_id,
    )
    appt.current_visit_status = visit_status
    db.add(event)
    if visit_status == "Completed":
        from app.services.visit_summary_service import create_visit_summary_on_completed

        await create_visit_summary_on_completed(db, appt, actor_id)

        from app.services.growth_service import queue_review_and_nps_requests

        clinic = await db.get(Clinic, appt.clinic_id)
        patient = await db.get(Patient, appt.patient_id)
        if clinic is not None and patient is not None:
            try:
                await queue_review_and_nps_requests(db, appt, clinic, patient)
            except Exception:
                logger.exception("Post-visit growth messages failed appointment=%s", appt.id)
    db.add(
        ActivityLog(
            clinic_id=appt.clinic_id,
            actor_user_id=actor_id,
            actor_type="user",
            action="visit.status_changed",
            target_type="appointment",
            target_id=str(appt.id),
            summary=f"Visit {current or 'none'} to {visit_status}",
            metadata_={"from": current, "to": visit_status},
        )
    )
    await db.commit()
    await db.refresh(appt)

    await publish_clinic_event(
        appt.clinic_id,
        "appointment.visit_status_changed",
        {
            "appointment_id": str(appt.id),
            "visit_status": visit_status,
            "patient_id": str(appt.patient_id),
        },
    )
    await notify_visit_status(
        db,
        clinic_id=appt.clinic_id,
        appointment_id=appt.id,
        patient_id=appt.patient_id,
        doctor_id=appt.doctor_id,
        visit_status=visit_status,
        actor_user_id=actor_id,
    )
    return appt


async def list_waiting_room(
    db: AsyncSession,
    clinic_id: uuid.UUID,
) -> list[Appointment]:
    now = datetime.now(MANILA)
    day_start = datetime(now.year, now.month, now.day, tzinfo=MANILA).astimezone(UTC)
    day_end = day_start + timedelta(days=1)

    result = await db.execute(
        select(Appointment)
        .where(
            Appointment.clinic_id == clinic_id,
            Appointment.scheduled_start >= day_start,
            Appointment.scheduled_start < day_end,
            Appointment.appointment_status.notin_(tuple(TERMINAL_STATUSES)),
        )
        .order_by(Appointment.scheduled_start)
    )
    return list(result.scalars().all())
