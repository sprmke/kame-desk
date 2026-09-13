import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.rate_limit import enforce_public_rate_limit
from app.models import ClinicMembership, DoctorProfile, Patient, ServiceFee, User
from app.schemas.appointment import AppointmentRead
from app.schemas.public import (
    PublicAppointmentRequest,
    PublicClinicRead,
    PublicDoctorRead,
    PublicSlotList,
)
from app.services import appointment_service, patient_service, slot_service
from app.services.clinic_service import get_clinic_by_slug

router = APIRouter(prefix="/public/clinics", tags=["public"])


async def _require_bookable_clinic(db: AsyncSession, slug: str):
    clinic = await get_clinic_by_slug(db, slug)
    from app.services.organization_service import is_clinic_enrollment_active

    if not await is_clinic_enrollment_active(db, clinic.id):
        raise HTTPException(status_code=404, detail="Clinic not found")
    return clinic


@router.get("/{slug}", response_model=PublicClinicRead)
async def get_public_clinic(
    slug: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> PublicClinicRead:
    enforce_public_rate_limit(request, slug)
    clinic = await _require_bookable_clinic(db, slug)
    doctors = await db.execute(
        select(DoctorProfile, User)
        .join(User, User.id == DoctorProfile.user_id)
        .where(DoctorProfile.clinic_id == clinic.id)
    )
    fees = await db.execute(
        select(ServiceFee).where(ServiceFee.clinic_id == clinic.id).order_by(ServiceFee.name)
    )
    return PublicClinicRead(
        name=clinic.name,
        slug=clinic.slug,
        address=clinic.address,
        contact_phone=clinic.contact_phone,
        contact_email=clinic.contact_email,
        working_hours=clinic.working_hours,
        holiday_dates=clinic.holiday_dates or [],
        default_appointment_duration_minutes=clinic.default_appointment_duration_minutes,
        doctors=[
            PublicDoctorRead(
                id=d.id,
                specialty=d.specialty,
                full_name=u.full_name,
            )
            for d, u in doctors.all()
        ],
        services=[{"name": f.name, "amount": str(f.amount)} for f in fees.scalars()],
    )


@router.get("/{slug}/available-slots", response_model=PublicSlotList)
async def public_available_slots(
    slug: str,
    request: Request,
    doctor_id: uuid.UUID,
    on_date: date = Query(..., alias="date"),
    duration_minutes: int | None = None,
    db: AsyncSession = Depends(get_db),
) -> PublicSlotList:
    enforce_public_rate_limit(request, slug)
    clinic = await _require_bookable_clinic(db, slug)
    slots = await slot_service.get_available_slots(db, clinic, doctor_id, on_date, duration_minutes)
    return PublicSlotList(slots=slots)


@router.post("/{slug}/appointment-requests", response_model=AppointmentRead)
async def public_appointment_request(
    slug: str,
    data: PublicAppointmentRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> AppointmentRead:
    enforce_public_rate_limit(request, slug)
    clinic = await _require_bookable_clinic(db, slug)

    owner = await db.execute(
        select(User)
        .join(ClinicMembership, ClinicMembership.user_id == User.id)
        .where(
            ClinicMembership.clinic_id == clinic.id,
            ClinicMembership.role == "owner",
            ClinicMembership.is_active.is_(True),
        )
        .limit(1)
    )
    owner_user = owner.scalar_one_or_none()
    if owner_user is None:
        raise HTTPException(status_code=503, detail="Clinic is not ready for bookings")

    patient = await _find_or_create_public_patient(db, clinic.id, data, owner_user.id)

    status = "Confirmed" if clinic.public_booking_auto_confirm else "Scheduled"
    from app.schemas.appointment import AppointmentCreate

    appt = await appointment_service.create_appointment(
        db,
        clinic,
        AppointmentCreate(
            patient_id=patient.id,
            doctor_id=data.doctor_id,
            scheduled_start=data.scheduled_start,
            scheduled_end=data.scheduled_end,
            reason_for_visit=data.reason_for_visit,
        ),
        owner_user.id,
        booking_source="public_link",
        initial_status=status,
    )
    row = AppointmentRead.model_validate(appt)
    return row


async def _find_or_create_public_patient(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    data: PublicAppointmentRequest,
    actor_id: uuid.UUID,
) -> Patient:
    if data.contact_number:
        result = await db.execute(
            select(Patient).where(
                Patient.clinic_id == clinic_id,
                Patient.contact_number == data.contact_number,
                Patient.is_archived.is_(False),
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

    from app.schemas.patient import PatientCreate

    return await patient_service.create_patient(
        db,
        clinic_id,
        PatientCreate(
            full_name=data.full_name,
            contact_number=data.contact_number,
            email=data.email,
        ),
        actor_id,
    )
