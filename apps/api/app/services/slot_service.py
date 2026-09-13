"""Compute open appointment slots for a doctor on a given date."""

import uuid
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Appointment, Clinic
from app.services.appointment_service import DAY_KEYS, MANILA, TERMINAL_STATUSES, _ensure_doctor

Slot = dict[str, str]


def _clinic_tz(clinic: Clinic) -> ZoneInfo:
    return MANILA if clinic.timezone == "Asia/Manila" else ZoneInfo(clinic.timezone)


def _parse_hm(value: str) -> tuple[int, int]:
    h, m = value.split(":")
    return int(h), int(m)


def _local_day_bounds(clinic: Clinic, on_date: date) -> tuple[datetime | None, datetime | None]:
    if not clinic.working_hours:
        return None, None
    day_key = DAY_KEYS[on_date.weekday()]
    hours = clinic.working_hours.get(day_key)
    if not hours or hours.get("closed"):
        return None, None
    tz = _clinic_tz(clinic)
    open_h, open_m = _parse_hm(hours["open"])
    close_h, close_m = _parse_hm(hours["close"])
    day_start = datetime(on_date.year, on_date.month, on_date.day, open_h, open_m, tzinfo=tz)
    day_end = datetime(on_date.year, on_date.month, on_date.day, close_h, close_m, tzinfo=tz)
    return day_start, day_end


def _overlaps(start: datetime, end: datetime, busy_start: datetime, busy_end: datetime) -> bool:
    return start < busy_end and busy_start < end


async def get_available_slots(
    db: AsyncSession,
    clinic: Clinic,
    doctor_id: uuid.UUID,
    on_date: date,
    duration_minutes: int | None = None,
) -> list[Slot]:
    if clinic.holiday_dates and on_date.isoformat() in clinic.holiday_dates:
        return []

    await _ensure_doctor(db, clinic.id, doctor_id)
    duration = duration_minutes or clinic.default_appointment_duration_minutes
    day_start, day_end = _local_day_bounds(clinic, on_date)
    if day_start is None or day_end is None:
        return []

    tz = _clinic_tz(clinic)
    range_start = datetime(on_date.year, on_date.month, on_date.day, tzinfo=tz)
    range_end = range_start + timedelta(days=1)

    result = await db.execute(
        select(Appointment).where(
            Appointment.clinic_id == clinic.id,
            Appointment.doctor_id == doctor_id,
            Appointment.scheduled_start >= range_start.astimezone(MANILA),
            Appointment.scheduled_start < range_end.astimezone(MANILA),
            Appointment.appointment_status.notin_(tuple(TERMINAL_STATUSES)),
        )
    )
    busy = list(result.scalars().all())

    slots: list[Slot] = []
    cursor = day_start
    delta = timedelta(minutes=duration)
    while cursor + delta <= day_end:
        slot_end = cursor + delta
        conflict = any(
            _overlaps(cursor, slot_end, b.scheduled_start, b.scheduled_end) for b in busy
        )
        if not conflict:
            slots.append(
                {
                    "scheduled_start": cursor.astimezone(MANILA).isoformat(),
                    "scheduled_end": slot_end.astimezone(MANILA).isoformat(),
                }
            )
        cursor += delta
    return slots
