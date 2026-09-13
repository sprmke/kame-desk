import uuid
from datetime import UTC, date, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import paginate, parse_sort
from app.models import (
    ActivityLog,
    Appointment,
    Clinic,
    Patient,
    PatientMedicalInfo,
    PatientRecall,
    SoapNote,
)
from app.services.notification_prefs import merged_preferences


async def list_clinic_recalls(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    status: str | None = "pending",
    *,
    q: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
    sort: str | None = None,
) -> tuple[list[PatientRecall], int]:
    query = select(PatientRecall).where(PatientRecall.clinic_id == clinic_id)
    if status:
        query = query.where(PatientRecall.status == status)
    if q and q.strip():
        term = f"%{q.strip()}%"
        query = query.join(Patient, Patient.id == PatientRecall.patient_id).where(
            Patient.full_name.ilike(term) | PatientRecall.source.ilike(term)
        )
    query = query.order_by(
        parse_sort(
            sort,
            {
                "due_date": PatientRecall.due_date,
                "created_at": PatientRecall.created_at,
                "status": PatientRecall.status,
            },
            "due_date",
        )
    )
    if page_size is None:
        result = await db.execute(query)
        items = list(result.scalars().unique().all())
        return items, len(items)
    return await paginate(db, query, page or 1, page_size)


async def update_recall_status(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    recall_id: uuid.UUID,
    status: str,
    actor_id: uuid.UUID,
) -> PatientRecall:
    if status not in ("pending", "contacted", "booked", "dismissed"):
        raise HTTPException(status_code=400, detail="Invalid recall status")
    result = await db.execute(
        select(PatientRecall).where(
            PatientRecall.id == recall_id,
            PatientRecall.clinic_id == clinic_id,
        )
    )
    recall = result.scalar_one_or_none()
    if recall is None:
        raise HTTPException(status_code=404, detail="Recall not found")
    recall.status = status
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor_id,
            actor_type="user",
            action="recall.status_changed",
            target_type="patient_recall",
            target_id=str(recall.id),
            summary=f"Recall marked {status}",
        )
    )
    await db.commit()
    await db.refresh(recall)
    return recall


async def _has_future_appointment(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    patient_id: uuid.UUID,
    after: date,
) -> bool:
    start = datetime.combine(after, datetime.min.time(), tzinfo=UTC)
    result = await db.execute(
        select(func.count())
        .select_from(Appointment)
        .where(
            Appointment.clinic_id == clinic_id,
            Appointment.patient_id == patient_id,
            Appointment.scheduled_start >= start,
            Appointment.appointment_status.notin_(("Cancelled", "No Show", "Rescheduled")),
        )
    )
    return int(result.scalar_one()) > 0


async def generate_recalls_from_follow_ups(db: AsyncSession) -> int:
    today = datetime.now(UTC).date()
    window_end = today + timedelta(days=30)
    result = await db.execute(
        select(SoapNote)
        .where(
            SoapNote.follow_up_date.isnot(None),
            SoapNote.follow_up_date <= window_end,
        )
        .order_by(SoapNote.follow_up_date)
    )
    notes = list(result.scalars().all())
    created = 0
    for note in notes:
        if note.follow_up_date is None:
            continue
        if await _has_future_appointment(db, note.clinic_id, note.patient_id, note.follow_up_date):
            continue
        existing = await db.execute(
            select(PatientRecall).where(
                PatientRecall.clinic_id == note.clinic_id,
                PatientRecall.patient_id == note.patient_id,
                PatientRecall.source == "follow_up_date",
                PatientRecall.due_date == note.follow_up_date,
            )
        )
        if existing.scalar_one_or_none():
            continue
        db.add(
            PatientRecall(
                clinic_id=note.clinic_id,
                patient_id=note.patient_id,
                source="follow_up_date",
                due_date=note.follow_up_date,
                status="pending",
                source_soap_note_id=note.id,
                created_at=datetime.now(UTC),
            )
        )
        created += 1
    if created:
        await db.commit()
    return created


async def generate_chronic_condition_recalls(db: AsyncSession) -> int:
    clinics = await db.execute(select(PatientMedicalInfo))
    created = 0
    today = datetime.now(UTC).date()
    for med in clinics.scalars().all():
        clinic = await db.get(Clinic, med.clinic_id)
        if clinic is None:
            continue
        prefs = merged_preferences(clinic.notification_preferences)
        rules = prefs.get("chronic_condition_rules") or []
        if not rules:
            continue
        conditions = {c.lower() for c in (med.chronic_conditions or [])}
        for rule in rules:
            cond = str(rule.get("condition", "")).lower()
            if not cond or cond not in conditions:
                continue
            months = int(rule.get("interval_months", 6))
            due = today + timedelta(days=months * 30)
            existing = await db.execute(
                select(PatientRecall).where(
                    PatientRecall.clinic_id == med.clinic_id,
                    PatientRecall.patient_id == med.patient_id,
                    PatientRecall.source == "chronic_condition_rule",
                    PatientRecall.due_date == due,
                )
            )
            if existing.scalar_one_or_none():
                continue
            if await _has_future_appointment(db, med.clinic_id, med.patient_id, today):
                continue
            db.add(
                PatientRecall(
                    clinic_id=med.clinic_id,
                    patient_id=med.patient_id,
                    source="chronic_condition_rule",
                    due_date=due,
                    status="pending",
                    created_at=datetime.now(UTC),
                )
            )
            created += 1
    if created:
        await db.commit()
    return created


async def generate_all_recalls(db: AsyncSession) -> dict[str, int]:
    follow = await generate_recalls_from_follow_ups(db)
    chronic = await generate_chronic_condition_recalls(db)
    if follow or chronic:
        db.add(
            ActivityLog(
                clinic_id=None,
                actor_user_id=None,
                actor_type="system",
                action="system.cron_run",
                target_type="recall_generation",
                target_id=None,
                summary="Recall generation run",
                metadata_={"follow_up": follow, "chronic": chronic},
            )
        )
        await db.commit()
    return {"follow_up": follow, "chronic": chronic}
