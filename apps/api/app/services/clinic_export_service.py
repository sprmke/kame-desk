import csv
import io
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ActivityLog, Appointment, Clinic, Patient, User
from app.models.user import ClinicMembership


def _log_export(db: AsyncSession, clinic_id: uuid.UUID, actor_id: uuid.UUID, kind: str) -> None:
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor_id,
            actor_type="user",
            action="clinic.data_exported",
            target_type="clinic",
            target_id=str(clinic_id),
            summary=f"Exported {kind} CSV",
            metadata_={"kind": kind},
        )
    )


async def export_patients_csv(db: AsyncSession, clinic_id: uuid.UUID, actor_id: uuid.UUID) -> str:
    result = await db.execute(
        select(Patient)
        .where(Patient.clinic_id == clinic_id, Patient.is_archived.is_(False))
        .order_by(Patient.patient_number)
    )
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["patient_number", "full_name", "birthdate", "sex", "contact_number", "email"])
    for p in result.scalars():
        writer.writerow(
            [
                p.patient_number,
                p.full_name,
                p.birthdate.isoformat() if p.birthdate else "",
                p.sex or "",
                p.contact_number or "",
                p.email or "",
            ]
        )
    _log_export(db, clinic_id, actor_id, "patients")
    await db.commit()
    return buf.getvalue()


async def export_appointments_csv(
    db: AsyncSession, clinic_id: uuid.UUID, actor_id: uuid.UUID
) -> str:
    result = await db.execute(
        select(Appointment, Patient)
        .join(Patient, Patient.id == Appointment.patient_id)
        .where(Appointment.clinic_id == clinic_id)
        .order_by(Appointment.scheduled_start)
    )
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "scheduled_start",
            "scheduled_end",
            "status",
            "patient_number",
            "patient_name",
            "reason_for_visit",
        ]
    )
    for appt, patient in result.all():
        writer.writerow(
            [
                appt.scheduled_start.isoformat(),
                appt.scheduled_end.isoformat(),
                appt.appointment_status,
                patient.patient_number,
                patient.full_name,
                appt.reason_for_visit or "",
            ]
        )
    _log_export(db, clinic_id, actor_id, "appointments")
    await db.commit()
    return buf.getvalue()


async def request_clinic_deletion(
    db: AsyncSession,
    clinic: Clinic,
    actor: User,
    membership: ClinicMembership,
) -> Clinic:
    if membership.role != "owner":
        raise HTTPException(status_code=403, detail="Only the owner can request deletion")
    if clinic.deletion_requested_at is not None:
        return clinic
    clinic.deletion_requested_at = datetime.now(UTC)
    db.add(
        ActivityLog(
            clinic_id=clinic.id,
            actor_user_id=actor.id,
            actor_type="user",
            action="clinic.deletion_requested",
            target_type="clinic",
            target_id=str(clinic.id),
            summary="Clinic data deletion requested",
        )
    )
    await db.commit()
    await db.refresh(clinic)
    from app.services.notification_service import notify_clinic_deletion_requested

    await notify_clinic_deletion_requested(
        db,
        clinic_id=clinic.id,
        actor_user_id=actor.id,
    )
    return clinic
