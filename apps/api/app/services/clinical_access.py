import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Clinic, ClinicMembership, DoctorProfile, User


async def assert_soap_read(
    db: AsyncSession,
    membership: ClinicMembership,
    clinic: Clinic,
) -> None:
    if membership.role in ("owner", "admin", "doctor"):
        return
    if membership.role == "reception" and clinic.reception_can_view_soap:
        return
    raise HTTPException(status_code=403, detail="Clinical notes access denied")


async def assert_soap_write(
    db: AsyncSession,
    membership: ClinicMembership,
    appointment_doctor_id: uuid.UUID,
    user: User,
) -> None:
    if membership.role not in ("doctor", "owner"):
        raise HTTPException(status_code=403, detail="Clinical write not allowed")
    if membership.role == "owner":
        return
    result = await db.execute(
        select(DoctorProfile).where(
            DoctorProfile.user_id == user.id,
            DoctorProfile.clinic_id == membership.clinic_id,
        )
    )
    doctor = result.scalar_one_or_none()
    if doctor is None or doctor.id != appointment_doctor_id:
        raise HTTPException(status_code=403, detail="Not the assigned doctor")


async def get_doctor_profile_for_user(
    db: AsyncSession,
    user: User,
    clinic_id: uuid.UUID,
) -> DoctorProfile | None:
    result = await db.execute(
        select(DoctorProfile).where(
            DoctorProfile.user_id == user.id,
            DoctorProfile.clinic_id == clinic_id,
        )
    )
    return result.scalar_one_or_none()


async def assert_prescription_read(membership: ClinicMembership) -> None:
    if membership.role in ("owner", "admin", "doctor"):
        return
    raise HTTPException(status_code=403, detail="Prescription access denied")


async def assert_clinical_notes_write(membership: ClinicMembership) -> None:
    if membership.role in ("doctor", "owner"):
        return
    raise HTTPException(status_code=403, detail="Clinical notes write not allowed")


async def assert_doctor_profile_write(
    membership: ClinicMembership,
    profile: DoctorProfile,
    user: User,
) -> None:
    if profile.clinic_id != membership.clinic_id:
        raise HTTPException(status_code=404, detail="Doctor not found")
    if membership.role in ("owner", "admin"):
        return
    if membership.role == "doctor" and profile.user_id == user.id:
        return
    raise HTTPException(status_code=403, detail="Not allowed to edit this doctor profile")


async def assert_prescription_write(
    db: AsyncSession,
    membership: ClinicMembership,
    user: User,
) -> DoctorProfile:
    doctor = await get_doctor_profile_for_user(db, user, membership.clinic_id)
    if doctor is None:
        raise HTTPException(
            status_code=403,
            detail="Doctor profile required to issue prescriptions",
        )
    if membership.role not in ("doctor", "owner"):
        raise HTTPException(status_code=403, detail="Prescription write not allowed")
    return doctor
