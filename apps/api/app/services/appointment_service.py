import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import paginate, parse_sort
from app.models import ActivityLog, Appointment, Clinic, DoctorProfile, Patient, Room, ServiceFee
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate
from app.services.notification_service import (
    notify_appointment_cancelled,
    notify_appointment_public_booked,
    notify_appointment_rescheduled,
)
from app.services.patient_service import get_patient
from app.services.realtime_service import broadcast_appointment_event
from app.services.reminder_service import (
    on_appointment_cancelled,
    on_appointment_created,
    on_appointment_rescheduled,
)

MANILA = ZoneInfo("Asia/Manila")
TERMINAL_STATUSES = {"Cancelled", "No Show", "Rescheduled"}
DAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def _day_key(dt: datetime, clinic: Clinic) -> str:
    tz = MANILA if clinic.timezone == "Asia/Manila" else ZoneInfo(clinic.timezone)
    local = dt.astimezone(tz)
    return DAY_KEYS[local.weekday()]


async def has_schedule_overlap(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    doctor_id: uuid.UUID,
    start: datetime,
    end: datetime,
    *,
    exclude_appointment_id: uuid.UUID | None = None,
) -> bool:
    query = select(Appointment.id).where(
        Appointment.clinic_id == clinic_id,
        Appointment.doctor_id == doctor_id,
        Appointment.appointment_status.notin_(TERMINAL_STATUSES),
        Appointment.scheduled_start < end,
        Appointment.scheduled_end > start,
    )
    if exclude_appointment_id is not None:
        query = query.where(Appointment.id != exclude_appointment_id)
    result = await db.execute(query.limit(1))
    return result.scalar_one_or_none() is not None


def validate_working_hours(clinic: Clinic, start: datetime, end: datetime) -> None:
    if not clinic.working_hours:
        return
    day = _day_key(start, clinic)
    hours = clinic.working_hours.get(day)
    if not hours or hours.get("closed"):
        raise HTTPException(status_code=400, detail="Clinic is closed at this time")
    local_start = start.astimezone(MANILA).strftime("%H:%M")
    local_end = end.astimezone(MANILA).strftime("%H:%M")
    if local_start < hours["open"] or local_end > hours["close"]:
        raise HTTPException(status_code=400, detail="Outside clinic working hours")


async def _ensure_doctor(
    db: AsyncSession, clinic_id: uuid.UUID, doctor_id: uuid.UUID
) -> DoctorProfile:
    result = await db.execute(
        select(DoctorProfile).where(
            DoctorProfile.id == doctor_id, DoctorProfile.clinic_id == clinic_id
        )
    )
    doctor = result.scalar_one_or_none()
    if doctor is None:
        raise HTTPException(status_code=400, detail="Doctor not found in clinic")
    return doctor


async def _ensure_room(db: AsyncSession, clinic_id: uuid.UUID, room_id: uuid.UUID) -> Room:
    result = await db.execute(
        select(Room).where(Room.id == room_id, Room.clinic_id == clinic_id, Room.is_active)
    )
    room = result.scalar_one_or_none()
    if room is None:
        raise HTTPException(status_code=400, detail="Room not found")
    return room


def _raise_if_double_book(exc: Exception) -> None:
    if isinstance(exc, IntegrityError):
        raise HTTPException(status_code=409, detail="Time slot unavailable") from exc
    lowered = str(exc).lower()
    if "exclusion" in lowered or "overlap" in lowered or "deadlock" in lowered:
        raise HTTPException(status_code=409, detail="Time slot unavailable") from exc
    raise exc


async def create_appointment(
    db: AsyncSession,
    clinic: Clinic,
    data: AppointmentCreate,
    actor_id: uuid.UUID,
    *,
    booking_source: str = "staff",
    initial_status: str = "Scheduled",
    skip_working_hours_check: bool = False,
    actor_type: str = "user",
) -> Appointment:
    if data.scheduled_end <= data.scheduled_start:
        raise HTTPException(status_code=400, detail="End must be after start")
    patient = await get_patient(db, clinic.id, data.patient_id)
    await _ensure_doctor(db, clinic.id, data.doctor_id)
    if data.room_id:
        await _ensure_room(db, clinic.id, data.room_id)
    if data.service_fee_id:
        fee = await db.get(ServiceFee, data.service_fee_id)
        if fee is None or fee.clinic_id != clinic.id:
            raise HTTPException(status_code=400, detail="Service type not found")
    if not skip_working_hours_check:
        validate_working_hours(clinic, data.scheduled_start, data.scheduled_end)

    appt = Appointment(
        clinic_id=clinic.id,
        patient_id=data.patient_id,
        doctor_id=data.doctor_id,
        room_id=data.room_id,
        service_fee_id=data.service_fee_id,
        scheduled_start=data.scheduled_start,
        scheduled_end=data.scheduled_end,
        reason_for_visit=data.reason_for_visit,
        notes=data.notes,
        appointment_status=initial_status,
        booking_source=booking_source,
        created_by_user_id=actor_id,
    )
    db.add(appt)
    try:
        await db.flush()
    except Exception as exc:
        await db.rollback()
        _raise_if_double_book(exc)
    db.add(
        ActivityLog(
            clinic_id=clinic.id,
            actor_user_id=actor_id,
            actor_type=actor_type,
            action="appointment.created",
            target_type="appointment",
            target_id=str(appt.id),
            summary="Appointment scheduled",
        )
    )
    await on_appointment_created(db, appt, clinic, patient)
    await db.commit()
    await db.refresh(appt)
    await broadcast_appointment_event(clinic.id, "appointment.created", appt.id)
    if booking_source in ("public_link", "patient_assistant"):
        await notify_appointment_public_booked(
            db,
            clinic_id=clinic.id,
            appointment_id=appt.id,
            patient_id=appt.patient_id,
            doctor_id=appt.doctor_id,
            needs_confirm=initial_status == "Scheduled",
        )
    return appt


async def list_appointments(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    doctor_id: uuid.UUID | None,
    patient_id: uuid.UUID | None,
    status_filter: str | None,
    start_from: datetime | None,
    start_to: datetime | None,
    *,
    booking_source: str | None = None,
    room_id: uuid.UUID | None = None,
    q: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
    sort: str | None = None,
) -> tuple[list[Appointment], int]:
    query = select(Appointment).where(Appointment.clinic_id == clinic_id)
    joined_patient = False
    sort_key = (sort or "start").split(":", 1)[0]
    if doctor_id:
        query = query.where(Appointment.doctor_id == doctor_id)
    if patient_id:
        query = query.where(Appointment.patient_id == patient_id)
    if status_filter:
        query = query.where(Appointment.appointment_status == status_filter)
    if start_from:
        query = query.where(Appointment.scheduled_start >= start_from)
    if start_to:
        query = query.where(Appointment.scheduled_start <= start_to)
    if booking_source:
        query = query.where(Appointment.booking_source == booking_source)
    if room_id:
        query = query.where(Appointment.room_id == room_id)
    if (q and q.strip()) or sort_key == "patient":
        query = query.join(Patient, Patient.id == Appointment.patient_id)
        joined_patient = True
    if q and q.strip():
        term = f"%{q.strip()}%"
        query = query.where(Patient.full_name.ilike(term))
    allowed = {
        "start": Appointment.scheduled_start,
        "status": Appointment.appointment_status,
        "created_at": Appointment.created_at,
        "patient": Patient.full_name if joined_patient else Appointment.scheduled_start,
    }
    query = query.order_by(parse_sort(sort, allowed, "start"))
    if page_size is None:
        result = await db.execute(query)
        items = list(result.scalars().unique().all())
        return items, len(items)
    return await paginate(db, query, page or 1, page_size)


async def get_appointment(
    db: AsyncSession, clinic_id: uuid.UUID, appt_id: uuid.UUID
) -> Appointment:
    result = await db.execute(
        select(Appointment).where(Appointment.id == appt_id, Appointment.clinic_id == clinic_id)
    )
    appt = result.scalar_one_or_none()
    if appt is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appt


def _validate_status_transition(old: str, new: str) -> None:
    if old == new:
        return
    if old in TERMINAL_STATUSES:
        raise HTTPException(status_code=400, detail="Appointment is terminal")
    allowed = {
        "Scheduled": {"Confirmed", "Cancelled", "Rescheduled", "No Show"},
        "Confirmed": {"Cancelled", "No Show", "Rescheduled"},
    }
    if new not in allowed.get(old, set()):
        raise HTTPException(status_code=400, detail="Invalid status transition")


async def update_appointment(
    db: AsyncSession,
    clinic: Clinic,
    appt: Appointment,
    data: AppointmentUpdate,
    actor_id: uuid.UUID,
    *,
    actor_type: str = "user",
) -> Appointment:
    old_status = appt.appointment_status
    payload = data.model_dump(exclude_unset=True)

    if "appointment_status" in payload:
        _validate_status_transition(old_status, payload["appointment_status"])
        appt.appointment_status = payload["appointment_status"]
    if "patient_id" in payload:
        await get_patient(db, clinic.id, payload["patient_id"])
        appt.patient_id = payload["patient_id"]
    if "doctor_id" in payload:
        await _ensure_doctor(db, clinic.id, payload["doctor_id"])
        appt.doctor_id = payload["doctor_id"]
    if "room_id" in payload:
        if payload["room_id"]:
            await _ensure_room(db, clinic.id, payload["room_id"])
        appt.room_id = payload["room_id"]
    if "service_fee_id" in payload:
        if payload["service_fee_id"]:
            fee = await db.get(ServiceFee, payload["service_fee_id"])
            if fee is None or fee.clinic_id != clinic.id:
                raise HTTPException(status_code=400, detail="Service type not found")
        appt.service_fee_id = payload["service_fee_id"]
    if "scheduled_start" in payload:
        appt.scheduled_start = payload["scheduled_start"]
    if "scheduled_end" in payload:
        appt.scheduled_end = payload["scheduled_end"]
    if "reason_for_visit" in payload:
        appt.reason_for_visit = payload["reason_for_visit"]
    if "notes" in payload:
        appt.notes = payload["notes"]

    if appt.scheduled_end <= appt.scheduled_start:
        raise HTTPException(status_code=400, detail="End must be after start")
    if appt.appointment_status not in TERMINAL_STATUSES:
        validate_working_hours(clinic, appt.scheduled_start, appt.scheduled_end)

    try:
        await db.flush()
    except Exception as exc:
        await db.rollback()
        _raise_if_double_book(exc)

    if appt.appointment_status != old_status:
        patient = await get_patient(db, clinic.id, appt.patient_id)
        if appt.appointment_status == "Cancelled":
            await on_appointment_cancelled(db, appt, clinic, patient)
        db.add(
            ActivityLog(
                clinic_id=appt.clinic_id,
                actor_user_id=actor_id,
                actor_type=actor_type,
                action="appointment.status_changed",
                target_type="appointment",
                target_id=str(appt.id),
                summary=f"Appointment {old_status} → {appt.appointment_status}",
                metadata_={"from": old_status, "to": appt.appointment_status},
            )
        )
        if appt.appointment_status == "Cancelled":
            await broadcast_appointment_event(appt.clinic_id, "appointment.cancelled", appt.id)
    elif "scheduled_start" in payload or "scheduled_end" in payload:
        patient = await get_patient(db, clinic.id, appt.patient_id)
        await on_appointment_rescheduled(db, appt, clinic, patient)
        db.add(
            ActivityLog(
                clinic_id=appt.clinic_id,
                actor_user_id=actor_id,
                actor_type=actor_type,
                action="appointment.updated",
                target_type="appointment",
                target_id=str(appt.id),
                summary="Appointment updated",
            )
        )
    else:
        db.add(
            ActivityLog(
                clinic_id=appt.clinic_id,
                actor_user_id=actor_id,
                actor_type=actor_type,
                action="appointment.updated",
                target_type="appointment",
                target_id=str(appt.id),
                summary="Appointment updated",
            )
        )
    await db.commit()
    await db.refresh(appt)
    if appt.appointment_status != old_status and appt.appointment_status == "Cancelled":
        await notify_appointment_cancelled(
            db,
            clinic_id=appt.clinic_id,
            appointment_id=appt.id,
            patient_id=appt.patient_id,
            doctor_id=appt.doctor_id,
            actor_user_id=actor_id,
            actor_type=actor_type,
        )
    return appt


async def reschedule_appointment(
    db: AsyncSession,
    clinic: Clinic,
    appt: Appointment,
    scheduled_start: datetime,
    scheduled_end: datetime,
    actor_id: uuid.UUID,
    *,
    actor_type: str = "user",
) -> Appointment:
    if appt.appointment_status in TERMINAL_STATUSES:
        raise HTTPException(status_code=400, detail="Appointment is terminal")
    if scheduled_end <= scheduled_start:
        raise HTTPException(status_code=400, detail="End must be after start")

    prior_slot = {
        "scheduled_start": appt.scheduled_start.isoformat(),
        "scheduled_end": appt.scheduled_end.isoformat(),
    }
    appt.scheduled_start = scheduled_start
    appt.scheduled_end = scheduled_end
    validate_working_hours(clinic, appt.scheduled_start, appt.scheduled_end)

    try:
        await db.flush()
    except Exception as exc:
        await db.rollback()
        _raise_if_double_book(exc)

    db.add(
        ActivityLog(
            clinic_id=appt.clinic_id,
            actor_user_id=actor_id,
            actor_type=actor_type,
            action="appointment.rescheduled",
            target_type="appointment",
            target_id=str(appt.id),
            summary="Appointment rescheduled",
            metadata_={"prior_slot": prior_slot},
        )
    )
    patient = await get_patient(db, clinic.id, appt.patient_id)
    await on_appointment_rescheduled(db, appt, clinic, patient)
    await db.commit()
    await db.refresh(appt)
    await broadcast_appointment_event(appt.clinic_id, "appointment.rescheduled", appt.id)
    await notify_appointment_rescheduled(
        db,
        clinic_id=appt.clinic_id,
        appointment_id=appt.id,
        patient_id=appt.patient_id,
        doctor_id=appt.doctor_id,
        new_start_iso=appt.scheduled_start.isoformat(),
        actor_user_id=actor_id,
        actor_type=actor_type,
    )
    return appt
