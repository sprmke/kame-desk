from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Appointment, ClinicMembership, Invoice, User
from app.services.clinical_access import get_doctor_profile_for_user


def assert_billing_write(membership: ClinicMembership) -> None:
    if membership.role in ("owner", "admin", "reception"):
        return
    raise HTTPException(status_code=403, detail="Billing write not allowed")


def assert_billing_read(membership: ClinicMembership) -> None:
    if membership.role in ("owner", "admin", "doctor", "reception"):
        return
    raise HTTPException(status_code=403, detail="Billing access denied")


def assert_billing_void(membership: ClinicMembership) -> None:
    if membership.role in ("owner", "admin"):
        return
    raise HTTPException(status_code=403, detail="Invoice void not allowed")


async def assert_invoice_read(
    db: AsyncSession,
    membership: ClinicMembership,
    invoice: Invoice,
    user: User,
) -> None:
    assert_billing_read(membership)
    if membership.role != "doctor":
        return
    doctor = await get_doctor_profile_for_user(db, user, membership.clinic_id)
    if doctor is None:
        raise HTTPException(status_code=403, detail="Billing access denied")
    if invoice.appointment_id is None:
        raise HTTPException(status_code=403, detail="Billing access denied")
    result = await db.execute(
        select(Appointment).where(
            Appointment.id == invoice.appointment_id,
            Appointment.clinic_id == membership.clinic_id,
        )
    )
    appt = result.scalar_one_or_none()
    if appt is None or appt.doctor_id != doctor.id:
        raise HTTPException(status_code=403, detail="Billing access denied")
