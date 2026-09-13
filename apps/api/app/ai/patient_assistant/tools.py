import uuid
from datetime import date
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.public import PublicAppointmentRequest
from app.services import slot_service


async def check_public_availability(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    doctor_id: uuid.UUID,
    on_date: date,
) -> dict[str, Any]:
    from app.models import Clinic

    clinic = await db.get(Clinic, clinic_id)
    if clinic is None:
        return {"slots": [], "total": 0}
    slots = await slot_service.get_available_slots(db, clinic, doctor_id, on_date)
    return {"slots": slots, "total": len(slots)}


async def book_public_appointment(
    db: AsyncSession,
    slug: str,
    data: PublicAppointmentRequest,
    owner_user_id: uuid.UUID,
) -> dict[str, Any]:
    from app.routers.public_booking import _find_or_create_public_patient
    from app.schemas.appointment import AppointmentCreate
    from app.services import appointment_service
    from app.services.clinic_service import get_clinic_by_slug

    clinic = await get_clinic_by_slug(db, slug)
    patient = await _find_or_create_public_patient(db, clinic.id, data, owner_user_id)
    status = "Confirmed" if clinic.public_booking_auto_confirm else "Scheduled"
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
        owner_user_id,
        booking_source="public_assistant",
        initial_status=status,
        actor_type="system",
    )
    return {
        "appointment_id": str(appt.id),
        "status": appt.appointment_status,
        "scheduled_start": appt.scheduled_start.isoformat(),
    }


def answer_clinic_faq(grounding: dict[str, Any], question: str) -> dict[str, Any]:
    q = question.lower()
    if "hour" in q or "open" in q or "schedule" in q:
        return {"answer": f"Hours: {grounding.get('working_hours')}", "grounded": True}
    if "phone" in q or "contact" in q or "call" in q:
        phone = grounding.get("contact_phone") or grounding.get("contact_email")
        if phone:
            return {"answer": f"Contact: {phone}", "grounded": True}
        return {"answer": "Please use the booking form or visit the clinic.", "grounded": False}
    if "fee" in q or "price" in q or "cost" in q:
        services = grounding.get("services") or []
        if services:
            names = ", ".join(f"{s['name']} ({s['amount']})" for s in services[:5])
            return {"answer": f"Listed fees: {names}", "grounded": True}
    if "hmo" in q or "insurance" in q:
        return {"answer": "Please contact the clinic about HMO coverage.", "grounded": True}
    return {"answer": "Please contact the clinic directly for that question.", "grounded": False}
