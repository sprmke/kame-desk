import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ActivityLog, Appointment, Clinic, Patient
from app.schemas.appointment import AppointmentCreate
from app.schemas.patient import PatientCreate
from app.services.appointment_service import create_appointment
from app.services.notification_service import notify_appointment_no_show
from app.services.patient_service import create_patient
from app.services.realtime_service import broadcast_appointment_event
from app.services.visit_service import transition_visit_status


async def create_walk_in(
    db: AsyncSession,
    clinic: Clinic,
    *,
    doctor_id: uuid.UUID,
    actor_id: uuid.UUID,
    patient_id: uuid.UUID | None = None,
    new_patient: PatientCreate | None = None,
    reason_for_visit: str | None = None,
) -> Appointment:
    if patient_id is None and new_patient is None:
        raise HTTPException(status_code=400, detail="Patient required")
    if patient_id and new_patient:
        raise HTTPException(status_code=400, detail="Provide patient_id or new_patient, not both")

    if new_patient:
        patient = await create_patient(db, clinic.id, new_patient, actor_id)
        patient_id = patient.id

    duration = timedelta(minutes=clinic.default_appointment_duration_minutes or 30)
    now = datetime.now(UTC)
    data = AppointmentCreate(
        patient_id=patient_id,
        doctor_id=doctor_id,
        scheduled_start=now,
        scheduled_end=now + duration,
        reason_for_visit=reason_for_visit,
    )
    appt = await create_appointment(
        db,
        clinic,
        data,
        actor_id,
        initial_status="Confirmed",
        skip_working_hours_check=True,
    )
    appt = await transition_visit_status(db, appt, "Arrived", actor_id)

    db.add(
        ActivityLog(
            clinic_id=clinic.id,
            actor_user_id=actor_id,
            actor_type="user",
            action="appointment.walk_in",
            target_type="appointment",
            target_id=str(appt.id),
            summary="Walk-in registered",
        )
    )
    await db.commit()
    await db.refresh(appt)
    await broadcast_appointment_event(clinic.id, "appointment.created", appt.id)
    return appt


async def mark_no_show(
    db: AsyncSession,
    appt: Appointment,
    actor_id: uuid.UUID,
) -> Appointment:
    if appt.appointment_status in ("Cancelled", "No Show", "Rescheduled"):
        raise HTTPException(status_code=400, detail="Appointment is terminal")
    now = datetime.now(UTC)
    if appt.scheduled_end > now:
        raise HTTPException(status_code=400, detail="Appointment has not ended yet")

    old_status = appt.appointment_status
    appt.appointment_status = "No Show"

    patient_result = await db.execute(select(Patient).where(Patient.id == appt.patient_id))
    patient = patient_result.scalar_one()
    patient.no_show_count += 1

    db.add(
        ActivityLog(
            clinic_id=appt.clinic_id,
            actor_user_id=actor_id,
            actor_type="user",
            action="appointment.no_show",
            target_type="appointment",
            target_id=str(appt.id),
            summary="Marked no show",
            metadata_={"from": old_status, "to": "No Show"},
        )
    )
    # Phase 11 extension point: enqueue recall/reminder job here.
    await db.commit()
    await db.refresh(appt)
    await broadcast_appointment_event(appt.clinic_id, "appointment.cancelled", appt.id)
    await notify_appointment_no_show(
        db,
        clinic_id=appt.clinic_id,
        appointment_id=appt.id,
        patient_id=appt.patient_id,
        doctor_id=appt.doctor_id,
        actor_user_id=actor_id,
    )
    return appt
