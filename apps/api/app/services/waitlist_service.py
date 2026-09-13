import uuid
from datetime import date

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ActivityLog, AppointmentWaitlist, DoctorProfile, Patient, User
from app.schemas.appointment import WaitlistCreate, WaitlistRead, WaitlistUpdate
from app.services.notification_service import notify_waitlist_created
from app.services.patient_service import get_patient


async def _ensure_doctor(db: AsyncSession, clinic_id: uuid.UUID, doctor_id: uuid.UUID) -> None:
    result = await db.execute(
        select(DoctorProfile).where(
            DoctorProfile.id == doctor_id, DoctorProfile.clinic_id == clinic_id
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=400, detail="Doctor not found in clinic")


async def list_waitlist(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    *,
    status: str | None = "waiting",
    doctor_id: uuid.UUID | None = None,
    preferred_date: date | None = None,
) -> list[AppointmentWaitlist]:
    q = select(AppointmentWaitlist).where(AppointmentWaitlist.clinic_id == clinic_id)
    if status:
        q = q.where(AppointmentWaitlist.status == status)
    if doctor_id:
        q = q.where(AppointmentWaitlist.doctor_id == doctor_id)
    if preferred_date:
        q = q.where(AppointmentWaitlist.preferred_date == preferred_date)
    result = await db.execute(q.order_by(AppointmentWaitlist.created_at))
    return list(result.scalars().all())


async def create_waitlist_entry(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    data: WaitlistCreate,
    actor_id: uuid.UUID,
) -> AppointmentWaitlist:
    await get_patient(db, clinic_id, data.patient_id)
    if data.doctor_id:
        await _ensure_doctor(db, clinic_id, data.doctor_id)
    entry = AppointmentWaitlist(
        clinic_id=clinic_id,
        patient_id=data.patient_id,
        doctor_id=data.doctor_id,
        preferred_date=data.preferred_date,
        notes=data.notes,
        status="waiting",
        created_by_user_id=actor_id,
    )
    db.add(entry)
    await db.flush()
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor_id,
            actor_type="user",
            action="waitlist.created",
            target_type="waitlist",
            target_id=str(entry.id),
            summary="Patient added to cancellation waitlist",
        )
    )
    await db.commit()
    await db.refresh(entry)
    await notify_waitlist_created(
        db,
        clinic_id=clinic_id,
        waitlist_id=entry.id,
        patient_id=entry.patient_id,
        actor_user_id=actor_id,
    )
    return entry


async def update_waitlist_entry(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    entry_id: uuid.UUID,
    data: WaitlistUpdate,
    actor_id: uuid.UUID,
) -> AppointmentWaitlist:
    result = await db.execute(
        select(AppointmentWaitlist).where(
            AppointmentWaitlist.id == entry_id,
            AppointmentWaitlist.clinic_id == clinic_id,
        )
    )
    entry = result.scalar_one_or_none()
    if entry is None:
        raise HTTPException(status_code=404, detail="Waitlist entry not found")
    payload = data.model_dump(exclude_unset=True)
    if "doctor_id" in payload and payload["doctor_id"]:
        await _ensure_doctor(db, clinic_id, payload["doctor_id"])
        entry.doctor_id = payload["doctor_id"]
    if "preferred_date" in payload:
        entry.preferred_date = payload["preferred_date"]
    if "notes" in payload:
        entry.notes = payload["notes"]
    if "status" in payload and payload["status"]:
        if entry.status != "waiting" and payload["status"] != entry.status:
            raise HTTPException(status_code=400, detail="Waitlist entry is already closed")
        entry.status = payload["status"]
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor_id,
            actor_type="user",
            action="waitlist.updated",
            target_type="waitlist",
            target_id=str(entry.id),
            summary="Waitlist entry updated",
        )
    )
    await db.commit()
    await db.refresh(entry)
    return entry


async def enrich_waitlist(db: AsyncSession, rows: list[AppointmentWaitlist]) -> list[WaitlistRead]:
    if not rows:
        return []
    patients = await db.execute(select(Patient).where(Patient.id.in_({r.patient_id for r in rows})))
    doctor_ids = {r.doctor_id for r in rows if r.doctor_id}
    doctor_map: dict[uuid.UUID, str] = {}
    if doctor_ids:
        doctors = await db.execute(
            select(DoctorProfile, User)
            .join(User, User.id == DoctorProfile.user_id)
            .where(DoctorProfile.id.in_(doctor_ids))
        )
        doctor_map = {d.id: u.full_name for d, u in doctors.all()}
    names = {p.id: p.full_name for p in patients.scalars()}
    out: list[WaitlistRead] = []
    for row in rows:
        item = WaitlistRead.model_validate(row)
        item.patient_name = names.get(row.patient_id)
        item.doctor_name = doctor_map.get(row.doctor_id) if row.doctor_id else None
        out.append(item)
    return out
