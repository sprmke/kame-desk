import uuid
from datetime import UTC, date, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import ClinicAiUsage, PatientMedicalInfo, PatientVital


async def _get_or_create_usage_row(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    usage_date: date,
) -> ClinicAiUsage:
    result = await db.execute(
        select(ClinicAiUsage).where(
            ClinicAiUsage.clinic_id == clinic_id,
            ClinicAiUsage.usage_date == usage_date,
        )
    )
    row = result.scalar_one_or_none()
    if row is not None:
        return row
    row = ClinicAiUsage(
        clinic_id=clinic_id,
        usage_date=usage_date,
        request_count=0,
        token_count=0,
    )
    db.add(row)
    await db.flush()
    return row


async def assert_ai_usage_available(db: AsyncSession, clinic_id: uuid.UUID) -> None:
    today = datetime.now(UTC).date()
    row = await _get_or_create_usage_row(db, clinic_id, today)
    if row.request_count >= settings.ai_daily_request_cap:
        raise HTTPException(
            status_code=429,
            detail="AI drafting unavailable today",
        )


async def list_ai_usage(db: AsyncSession, clinic_id: uuid.UUID, *, days: int = 30) -> dict:
    start = datetime.now(UTC).date() - timedelta(days=days)
    result = await db.execute(
        select(ClinicAiUsage)
        .where(
            ClinicAiUsage.clinic_id == clinic_id,
            ClinicAiUsage.usage_date >= start,
        )
        .order_by(ClinicAiUsage.usage_date.desc())
    )
    rows = list(result.scalars().all())
    return {
        "days": [
            {
                "date": row.usage_date.isoformat(),
                "requests": row.request_count,
                "tokens": row.token_count,
            }
            for row in rows
        ],
        "request_total": sum(row.request_count for row in rows),
        "daily_cap": settings.ai_daily_request_cap,
    }


async def record_ai_usage(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    token_count: int = 0,
) -> None:
    today = datetime.now(UTC).date()
    row = await _get_or_create_usage_row(db, clinic_id, today)
    row.request_count += 1
    row.token_count += max(0, token_count)
    await db.commit()


async def build_visit_vitals_summary(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    patient_id: uuid.UUID,
) -> str | None:
    result = await db.execute(
        select(PatientVital)
        .where(PatientVital.patient_id == patient_id, PatientVital.clinic_id == clinic_id)
        .order_by(PatientVital.recorded_at.desc())
        .limit(1)
    )
    vital = result.scalar_one_or_none()
    if vital is None:
        return None
    parts: list[str] = []
    if vital.blood_pressure:
        parts.append(f"BP {vital.blood_pressure}")
    if vital.heart_rate is not None:
        parts.append(f"HR {vital.heart_rate}")
    if vital.temperature_c is not None:
        parts.append(f"Temp {vital.temperature_c} C")
    if vital.weight_kg is not None:
        parts.append(f"Weight {vital.weight_kg} kg")
    if vital.height_cm is not None:
        parts.append(f"Height {vital.height_cm} cm")
    if vital.respiratory_rate is not None:
        parts.append(f"RR {vital.respiratory_rate}")
    if vital.spo2 is not None:
        parts.append(f"SpO2 {vital.spo2}%")
    return ", ".join(parts) if parts else None


async def load_chronic_conditions(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    patient_id: uuid.UUID,
) -> list[str]:
    result = await db.execute(
        select(PatientMedicalInfo).where(
            PatientMedicalInfo.patient_id == patient_id,
            PatientMedicalInfo.clinic_id == clinic_id,
        )
    )
    info = result.scalar_one_or_none()
    if info is None or not info.chronic_conditions:
        return []
    return [str(c) for c in info.chronic_conditions]
