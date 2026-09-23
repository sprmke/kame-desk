"""Compute open appointment slots for a doctor on a given date."""

import uuid
from datetime import UTC, date, datetime, timedelta
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


def _at_local(clinic: Clinic, on_date: date, hm: str) -> datetime:
    tz = _clinic_tz(clinic)
    hour, minute = _parse_hm(hm)
    return datetime(on_date.year, on_date.month, on_date.day, hour, minute, tzinfo=tz)


def _day_hours(clinic: Clinic, on_date: date) -> dict | None:
    if not clinic.working_hours:
        return None
    day_key = DAY_KEYS[on_date.weekday()]
    hours = clinic.working_hours.get(day_key)
    if not hours or hours.get("closed"):
        return None
    return hours


def _local_day_bounds(clinic: Clinic, on_date: date) -> tuple[datetime | None, datetime | None]:
    hours = _day_hours(clinic, on_date)
    if hours is None:
        return None, None
    return _at_local(clinic, on_date, hours["open"]), _at_local(clinic, on_date, hours["close"])


def _local_breaks(clinic: Clinic, on_date: date) -> list[tuple[datetime, datetime]]:
    hours = _day_hours(clinic, on_date)
    if hours is None:
        return []
    out: list[tuple[datetime, datetime]] = []
    for item in hours.get("breaks") or []:
        start_raw = item.get("start") if isinstance(item, dict) else None
        end_raw = item.get("end") if isinstance(item, dict) else None
        if not start_raw or not end_raw:
            continue
        try:
            start = _at_local(clinic, on_date, start_raw)
            end = _at_local(clinic, on_date, end_raw)
        except (KeyError, ValueError):
            continue
        if start < end:
            out.append((start, end))
    return out


def _overlaps(start: datetime, end: datetime, busy_start: datetime, busy_end: datetime) -> bool:
    return start < busy_end and busy_start < end


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def slot_matches(slots: list[Slot], start: datetime, end: datetime) -> bool:
    start_utc = _as_utc(start)
    end_utc = _as_utc(end)
    for slot in slots:
        slot_start = datetime.fromisoformat(slot["scheduled_start"])
        slot_end = datetime.fromisoformat(slot["scheduled_end"])
        if _as_utc(slot_start) == start_utc and _as_utc(slot_end) == end_utc:
            return True
    return False


def _within_advance_window(clinic: Clinic, on_date: date) -> bool:
    today = datetime.now(_clinic_tz(clinic)).date()
    days = clinic.advance_booking_days or 90
    return on_date <= today + timedelta(days=days)


async def get_available_slots(
    db: AsyncSession,
    clinic: Clinic,
    doctor_id: uuid.UUID,
    on_date: date,
    duration_minutes: int | None = None,
) -> list[Slot]:
    if clinic.holiday_dates and on_date.isoformat() in clinic.holiday_dates:
        return []
    if not _within_advance_window(clinic, on_date):
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
    breaks = _local_breaks(clinic, on_date)
    pad = timedelta(minutes=clinic.slot_buffer_minutes or 0)

    slots: list[Slot] = []
    cursor = day_start
    delta = timedelta(minutes=duration)
    while cursor + delta <= day_end:
        slot_end = cursor + delta
        in_break = any(_overlaps(cursor, slot_end, br_start, br_end) for br_start, br_end in breaks)
        conflict = any(
            _overlaps(cursor, slot_end, b.scheduled_start - pad, b.scheduled_end + pad)
            for b in busy
        )
        if not in_break and not conflict:
            slots.append(
                {
                    "scheduled_start": cursor.astimezone(MANILA).isoformat(),
                    "scheduled_end": slot_end.astimezone(MANILA).isoformat(),
                }
            )
        cursor += delta
    return slots
