import uuid
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.security import create_patient_access_token, hash_refresh_token
from app.models import (
    ActivityLog,
    Appointment,
    Clinic,
    DoctorProfile,
    Invoice,
    Patient,
    PatientFile,
    PatientPortalToken,
    PatientVital,
    SoapNote,
    User,
)
from app.services.clinic_service import get_clinic_by_slug
from app.services.email_service import send_account_email
from app.services.secrets_crypto import decrypt_json
from app.services.sms_service import normalize_ph_e164, send_twilio_sms
from app.services.storage_service import create_presigned_download

LOGIN_TOKEN_TTL = timedelta(minutes=15)
TWO_PLACES = Decimal("0.01")


def _money(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def _phone_candidates(raw: str) -> list[str]:
    candidates = {raw.strip()}
    try:
        normalized = normalize_ph_e164(raw)
        candidates.add(normalized)
        digits = normalized.removeprefix("+63")
        if digits:
            candidates.add(f"0{digits}")
    except ValueError:
        pass
    return [c for c in candidates if c]


async def _find_matching_patients(
    db: AsyncSession, clinic_id: uuid.UUID, identifier: str
) -> list[Patient]:
    identifier = identifier.strip()
    if not identifier:
        return []
    if "@" in identifier:
        result = await db.execute(
            select(Patient).where(
                Patient.clinic_id == clinic_id,
                Patient.is_archived.is_(False),
                Patient.email.isnot(None),
                Patient.email.ilike(identifier),
            )
        )
        return list(result.scalars().all())

    candidates = _phone_candidates(identifier)
    if not candidates:
        return []
    result = await db.execute(
        select(Patient).where(
            Patient.clinic_id == clinic_id,
            Patient.is_archived.is_(False),
            Patient.contact_number.in_(candidates),
        )
    )
    return list(result.scalars().all())


async def _issue_login_token(db: AsyncSession, patient: Patient, delivery_channel: str) -> str:
    await db.execute(
        update(PatientPortalToken)
        .where(
            PatientPortalToken.patient_id == patient.id,
            PatientPortalToken.purpose == "login",
            PatientPortalToken.used_at.is_(None),
        )
        .values(used_at=datetime.now(UTC))
    )
    raw = f"{uuid.uuid4().hex}{uuid.uuid4().hex}"
    db.add(
        PatientPortalToken(
            patient_id=patient.id,
            clinic_id=patient.clinic_id,
            purpose="login",
            token_hash=hash_refresh_token(raw),
            delivery_channel=delivery_channel,
            expires_at=datetime.now(UTC) + LOGIN_TOKEN_TTL,
            created_at=datetime.now(UTC),
        )
    )
    await db.flush()
    return raw


async def request_login_link(db: AsyncSession, clinic_slug: str, identifier: str) -> None:
    """Always completes without revealing whether the identifier matched a patient."""
    try:
        clinic = await get_clinic_by_slug(db, clinic_slug)
    except HTTPException:
        return

    patients = await _find_matching_patients(db, clinic.id, identifier)
    for patient in patients:
        via_email = "@" in identifier and patient.email
        if via_email:
            raw = await _issue_login_token(db, patient, "email")
            link = f"{settings.web_base_url}/patient-portal/{clinic.slug}/verify?token={raw}"
            send_account_email(
                patient.email,
                f"Your {clinic.name} patient portal login link",
                f"Use this link to access your patient portal. It expires in 15 minutes and can only be used once.\n\n{link}\n",
            )
        elif patient.contact_number and clinic.twilio_credentials_encrypted:
            raw = await _issue_login_token(db, patient, "sms")
            link = f"{settings.web_base_url}/patient-portal/{clinic.slug}/verify?token={raw}"
            try:
                creds = decrypt_json(clinic.twilio_credentials_encrypted)
                await send_twilio_sms(
                    to=patient.contact_number,
                    body=f"{clinic.name} patient portal login link (expires in 15 min): {link}",
                    creds=creds,
                )
            except Exception:
                pass
    await db.commit()


async def verify_login_link(db: AsyncSession, raw_token: str) -> tuple[str, uuid.UUID, uuid.UUID]:
    token_hash = hash_refresh_token(raw_token)
    result = await db.execute(
        select(PatientPortalToken).where(
            PatientPortalToken.token_hash == token_hash,
            PatientPortalToken.purpose == "login",
        )
    )
    row = result.scalar_one_or_none()
    if row is None or row.used_at is not None or row.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=400, detail="Invalid or expired login link")

    patient = await db.get(Patient, row.patient_id)
    if patient is None or patient.is_archived:
        raise HTTPException(status_code=400, detail="Invalid or expired login link")

    row.used_at = datetime.now(UTC)
    access_token = create_patient_access_token(patient.id, patient.clinic_id)
    db.add(
        ActivityLog(
            clinic_id=patient.clinic_id,
            actor_user_id=None,
            actor_type="patient",
            action="patient_portal.login",
            target_type="patient",
            target_id=str(patient.id),
            summary=f"{patient.full_name} logged into the patient portal",
        )
    )
    await db.commit()
    return access_token, patient.id, patient.clinic_id


async def get_me(db: AsyncSession, patient: Patient) -> dict:
    clinic = await db.get(Clinic, patient.clinic_id)
    return {
        "id": patient.id,
        "clinic_id": patient.clinic_id,
        "clinic_name": clinic.name if clinic else "",
        "full_name": patient.full_name,
        "email": patient.email,
        "contact_number": patient.contact_number,
    }


async def list_visits(db: AsyncSession, patient: Patient) -> list[dict]:
    result = await db.execute(
        select(Appointment, DoctorProfile, User)
        .join(DoctorProfile, DoctorProfile.id == Appointment.doctor_id)
        .join(User, User.id == DoctorProfile.user_id)
        .where(
            Appointment.patient_id == patient.id,
            Appointment.clinic_id == patient.clinic_id,
        )
        .order_by(Appointment.scheduled_start.desc())
    )
    return [
        {
            "id": appt.id,
            "scheduled_start": appt.scheduled_start,
            "doctor_name": user.full_name,
            "reason_for_visit": appt.reason_for_visit,
            "appointment_status": appt.appointment_status,
            "current_visit_status": appt.current_visit_status,
        }
        for appt, _doctor, user in result.all()
    ]


async def get_chart_summary(db: AsyncSession, patient: Patient) -> dict:
    soap_result = await db.execute(
        select(SoapNote, User, Appointment)
        .join(User, User.id == SoapNote.created_by_user_id)
        .join(Appointment, Appointment.id == SoapNote.appointment_id)
        .where(
            SoapNote.patient_id == patient.id,
            SoapNote.clinic_id == patient.clinic_id,
            SoapNote.signed_at.isnot(None),
        )
        .order_by(Appointment.scheduled_start.desc())
    )
    diagnoses = [
        {
            "visit_date": appt.scheduled_start,
            "doctor_name": user.full_name,
            "diagnosis_primary": note.diagnosis_primary,
            "diagnosis_secondary": note.diagnosis_secondary,
            "icd10_codes": note.icd10_codes,
            "follow_up_date": note.follow_up_date,
        }
        for note, user, appt in soap_result.all()
        if note.diagnosis_primary or note.diagnosis_secondary
    ]

    vitals_result = await db.execute(
        select(PatientVital)
        .where(
            PatientVital.patient_id == patient.id,
            PatientVital.clinic_id == patient.clinic_id,
        )
        .order_by(PatientVital.recorded_at.desc())
        .limit(50)
    )
    vitals = list(vitals_result.scalars().all())
    return {"diagnoses": diagnoses, "vitals": vitals}


async def list_invoices(db: AsyncSession, patient: Patient) -> dict:
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.payments))
        .where(
            Invoice.patient_id == patient.id,
            Invoice.clinic_id == patient.clinic_id,
            Invoice.status != "draft",
        )
        .order_by(Invoice.created_at.desc())
    )
    invoices = list(result.scalars().all())
    items = []
    total_balance = Decimal("0")
    for inv in invoices:
        paid = _money(sum((p.amount for p in inv.payments), Decimal("0")))
        balance = _money(inv.total - paid)
        if inv.status in ("issued", "partially_paid"):
            total_balance += balance
        items.append(
            {
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "status": inv.status,
                "total": inv.total,
                "amount_paid": paid,
                "balance": balance,
                "issued_at": inv.issued_at,
            }
        )
    return {"items": items, "total_balance": _money(total_balance)}


async def list_documents(db: AsyncSession, patient: Patient) -> list[PatientFile]:
    result = await db.execute(
        select(PatientFile)
        .where(
            PatientFile.patient_id == patient.id,
            PatientFile.clinic_id == patient.clinic_id,
        )
        .order_by(PatientFile.uploaded_at.desc())
    )
    return list(result.scalars().all())


async def get_document_download(db: AsyncSession, patient: Patient, file_id: uuid.UUID) -> str:
    result = await db.execute(
        select(PatientFile).where(
            PatientFile.id == file_id,
            PatientFile.patient_id == patient.id,
            PatientFile.clinic_id == patient.clinic_id,
        )
    )
    file = result.scalar_one_or_none()
    if file is None:
        raise HTTPException(status_code=404, detail="Document not found")
    url = create_presigned_download(file.r2_key)
    db.add(
        ActivityLog(
            clinic_id=patient.clinic_id,
            actor_user_id=None,
            actor_type="patient",
            action="patient_portal.document_downloaded",
            target_type="patient_file",
            target_id=str(file.id),
            summary=f"{patient.full_name} downloaded a document from the patient portal",
        )
    )
    await db.commit()
    return url
