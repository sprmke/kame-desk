import uuid
from datetime import datetime, timedelta
from typing import Literal

from dateutil.rrule import rrulestr
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ActivityLog, Appointment, AppointmentSeries, Clinic
from app.services.appointment_service import TERMINAL_STATUSES, validate_working_hours
from app.services.patient_service import get_patient

EXPAND_HORIZON_DAYS = 90
SeriesScope = Literal["this", "following", "all"]


def parse_occurrences(
    series: AppointmentSeries,
    *,
    horizon_days: int = EXPAND_HORIZON_DAYS,
    after_index: int | None = None,
) -> list[tuple[int, datetime, datetime]]:
    """Return (occurrence_index, start, end) tuples within the expansion window."""
    window_end = series.series_start + timedelta(days=horizon_days)
    if series.series_end and series.series_end < window_end:
        window_end = series.series_end

    rule = rrulestr(series.rrule_string, dtstart=series.series_start)
    duration = timedelta(minutes=series.duration_minutes)
    results: list[tuple[int, datetime, datetime]] = []
    for idx, start in enumerate(rule):
        if start > window_end:
            break
        if after_index is not None and idx < after_index:
            continue
        if series.series_end and start > series.series_end:
            break
        end = start + duration
        results.append((idx, start, end))
    return results


async def _slot_taken(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    doctor_id: uuid.UUID,
    start: datetime,
    end: datetime,
) -> bool:
    result = await db.execute(
        select(Appointment.id)
        .where(
            Appointment.clinic_id == clinic_id,
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_status.notin_(tuple(TERMINAL_STATUSES)),
            Appointment.scheduled_start < end,
            Appointment.scheduled_end > start,
        )
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


async def expand_recurring_series(
    db: AsyncSession,
    series_id: uuid.UUID,
    *,
    horizon_days: int = EXPAND_HORIZON_DAYS,
    actor_id: uuid.UUID | None = None,
) -> dict:
    result = await db.execute(select(AppointmentSeries).where(AppointmentSeries.id == series_id))
    series = result.scalar_one_or_none()
    if series is None:
        raise HTTPException(status_code=404, detail="Series not found")

    clinic_result = await db.execute(select(Clinic).where(Clinic.id == series.clinic_id))
    clinic = clinic_result.scalar_one()

    existing = await db.execute(
        select(Appointment.series_occurrence_index).where(
            Appointment.series_id == series_id,
            Appointment.series_occurrence_index.is_not(None),
        )
    )
    existing_indexes = {row[0] for row in existing.all()}

    created = 0
    conflicts: list[dict] = []

    for idx, start, end in parse_occurrences(series, horizon_days=horizon_days):
        if idx in existing_indexes:
            continue
        try:
            validate_working_hours(clinic, start, end)
        except HTTPException as exc:
            conflicts.append(
                {
                    "occurrence_index": idx,
                    "scheduled_start": start.isoformat(),
                    "detail": exc.detail,
                }
            )
            continue

        if await _slot_taken(db, series.clinic_id, series.doctor_id, start, end):
            conflicts.append(
                {
                    "occurrence_index": idx,
                    "scheduled_start": start.isoformat(),
                    "detail": "Time slot unavailable",
                }
            )
            continue

        appt = Appointment(
            clinic_id=series.clinic_id,
            patient_id=series.patient_id,
            doctor_id=series.doctor_id,
            scheduled_start=start,
            scheduled_end=end,
            reason_for_visit=series.reason_for_visit,
            appointment_status="Confirmed",
            booking_source="staff",
            created_by_user_id=actor_id or series.created_by_user_id,
            series_id=series.id,
            series_occurrence_index=idx,
        )
        db.add(appt)
        await db.flush()
        created += 1

    if created:
        db.add(
            ActivityLog(
                clinic_id=series.clinic_id,
                actor_user_id=actor_id or series.created_by_user_id,
                actor_type="user" if actor_id else "system",
                action="appointment_series.expanded",
                target_type="appointment_series",
                target_id=str(series.id),
                summary=f"Expanded series ({created} new occurrences)",
                metadata_={"created": created, "conflicts": len(conflicts)},
            )
        )
    await db.commit()
    return {"created": created, "conflicts": conflicts}


async def create_appointment_series(
    db: AsyncSession,
    clinic: Clinic,
    *,
    patient_id: uuid.UUID,
    doctor_id: uuid.UUID,
    rrule_string: str,
    series_start: datetime,
    duration_minutes: int,
    actor_id: uuid.UUID,
    series_end: datetime | None = None,
    reason_for_visit: str | None = None,
) -> tuple[AppointmentSeries, dict]:
    await get_patient(db, clinic.id, patient_id)

    series = AppointmentSeries(
        clinic_id=clinic.id,
        patient_id=patient_id,
        doctor_id=doctor_id,
        rrule_string=rrule_string,
        series_start=series_start,
        series_end=series_end,
        duration_minutes=duration_minutes,
        reason_for_visit=reason_for_visit,
        created_by_user_id=actor_id,
    )
    db.add(series)
    await db.flush()

    db.add(
        ActivityLog(
            clinic_id=clinic.id,
            actor_user_id=actor_id,
            actor_type="user",
            action="appointment_series.created",
            target_type="appointment_series",
            target_id=str(series.id),
            summary="Recurring series created",
        )
    )
    await db.commit()
    await db.refresh(series)

    expansion = await expand_recurring_series(db, series.id, actor_id=actor_id)
    from app.core.arq_enqueue import enqueue_expand_recurring_series

    await enqueue_expand_recurring_series(series.id)
    return series, expansion


async def apply_series_scope(
    db: AsyncSession,
    appt: Appointment,
    scope: SeriesScope,
) -> list[Appointment]:
    if scope == "this" or appt.series_id is None:
        return [appt]

    q = select(Appointment).where(
        Appointment.series_id == appt.series_id,
        Appointment.appointment_status.notin_(("Cancelled", "No Show", "Rescheduled")),
    )
    if scope == "following" and appt.series_occurrence_index is not None:
        q = q.where(Appointment.series_occurrence_index >= appt.series_occurrence_index)
    result = await db.execute(q.order_by(Appointment.series_occurrence_index))
    return list(result.scalars().all())
