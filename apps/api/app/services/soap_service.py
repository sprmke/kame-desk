import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ActivityLog, Clinic, ClinicMembership, DoctorProfile, Patient, SoapNote, User
from app.schemas.soap import SoapNoteCreate
from app.services.appointment_service import get_appointment
from app.services.clinical_access import assert_soap_write


async def _next_version(db: AsyncSession, appointment_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.coalesce(func.max(SoapNote.version_number), 0)).where(
            SoapNote.appointment_id == appointment_id
        )
    )
    current = result.scalar_one()
    return int(current) + 1


def _normalize_specialty_data(data: dict | None, template_key: str | None) -> dict | None:
    if data is None:
        return None
    out = dict(data)
    out.setdefault("schema_version", 1)
    out.setdefault("template_key", template_key or "general")
    return out


async def create_soap_version(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    appointment_id: uuid.UUID,
    data: SoapNoteCreate,
    actor: User,
    membership: ClinicMembership,
    *,
    actor_type: str = "user",
) -> SoapNote:
    appt = await get_appointment(db, clinic_id, appointment_id)
    await assert_soap_write(db, membership, appt.doctor_id, actor)

    if data.client_draft_token:
        existing = await db.execute(
            select(SoapNote).where(
                SoapNote.appointment_id == appointment_id,
                SoapNote.client_draft_token == data.client_draft_token,
            )
        )
        existing_note = existing.scalar_one_or_none()
        if existing_note is not None:
            # Safe retry of a queued offline save (e.g. flushed twice after a
            # flaky reconnect) — return the already-saved version instead of
            # creating a duplicate.
            return existing_note

    version = await _next_version(db, appointment_id)
    note = SoapNote(
        appointment_id=appt.id,
        patient_id=appt.patient_id,
        doctor_id=appt.doctor_id,
        clinic_id=clinic_id,
        version_number=version,
        subjective=data.subjective,
        objective=data.objective,
        assessment=data.assessment,
        plan=data.plan,
        diagnosis_primary=data.diagnosis_primary,
        diagnosis_secondary=data.diagnosis_secondary,
        icd10_codes=data.icd10_codes,
        follow_up_date=data.follow_up_date,
        specialty_template_key=data.specialty_template_key,
        specialty_data=_normalize_specialty_data(data.specialty_data, data.specialty_template_key),
        created_by_user_id=actor.id,
        created_at=datetime.now(UTC),
        client_draft_token=data.client_draft_token,
    )
    db.add(note)
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor.id,
            actor_type=actor_type,
            action="soap.version_created",
            target_type="appointment",
            target_id=str(appt.id),
            summary=f"SOAP v{version} saved",
            metadata_={"version": version},
        )
    )
    await db.commit()
    await db.refresh(note)

    from app.core.arq_enqueue import enqueue_generate_soap_embedding

    await enqueue_generate_soap_embedding(note.id)

    return note


async def list_soap_versions(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    appointment_id: uuid.UUID,
) -> list[SoapNote]:
    await get_appointment(db, clinic_id, appointment_id)
    result = await db.execute(
        select(SoapNote)
        .where(SoapNote.appointment_id == appointment_id, SoapNote.clinic_id == clinic_id)
        .order_by(SoapNote.version_number.desc())
    )
    return list(result.scalars().all())


async def get_soap_version(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    appointment_id: uuid.UUID,
    version: int | None = None,
) -> SoapNote:
    await get_appointment(db, clinic_id, appointment_id)
    q = select(SoapNote).where(
        SoapNote.appointment_id == appointment_id,
        SoapNote.clinic_id == clinic_id,
    )
    if version is not None:
        q = q.where(SoapNote.version_number == version)
    else:
        q = q.order_by(SoapNote.version_number.desc()).limit(1)
    result = await db.execute(q)
    note = result.scalar_one_or_none()
    if note is None:
        raise HTTPException(status_code=404, detail="SOAP note not found")
    return note


async def sign_soap_version(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    appointment_id: uuid.UUID,
    version: int,
    actor: User,
    membership: ClinicMembership,
) -> SoapNote:
    note = await get_soap_version(db, clinic_id, appointment_id, version)
    await assert_soap_write(db, membership, note.doctor_id, actor)
    if note.signed_at:
        return note

    doctor_result = await db.execute(
        select(DoctorProfile).where(DoctorProfile.id == note.doctor_id)
    )
    doctor = doctor_result.scalar_one_or_none()
    signature_url = doctor.signature_image_key if doctor else None

    note.signed_at = datetime.now(UTC)
    note.signature_image_url = signature_url
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor.id,
            actor_type="user",
            action="soap.signed",
            target_type="appointment",
            target_id=str(appointment_id),
            summary=f"SOAP v{version} signed",
            metadata_={"version": version},
        )
    )
    await db.commit()
    await db.refresh(note)
    return note


def render_soap_pdf(
    clinic: Clinic,
    patient: Patient,
    note: SoapNote,
    doctor_name: str,
) -> bytes:
    from io import BytesIO

    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - inch

    c.setFont("Helvetica-Bold", 14)
    c.drawString(inch, y, clinic.name)
    y -= 0.25 * inch
    c.setFont("Helvetica", 10)
    if clinic.address:
        c.drawString(inch, y, clinic.address)
        y -= 0.2 * inch

    c.setFont("Helvetica-Bold", 12)
    y -= 0.15 * inch
    c.drawString(inch, y, f"SOAP Note - {patient.full_name}")
    y -= 0.2 * inch
    c.setFont("Helvetica", 10)
    c.drawString(inch, y, f"Version {note.version_number} - Dr. {doctor_name}")
    y -= 0.15 * inch
    if note.follow_up_date:
        c.drawString(inch, y, f"Follow-up: {note.follow_up_date.isoformat()}")
        y -= 0.15 * inch

    sections = [
        ("Subjective", note.subjective),
        ("Objective", note.objective),
        ("Assessment", note.assessment),
        ("Plan", note.plan),
    ]
    for title, body in sections:
        y -= 0.2 * inch
        if y < inch:
            c.showPage()
            y = height - inch
        c.setFont("Helvetica-Bold", 11)
        c.drawString(inch, y, title)
        y -= 0.18 * inch
        c.setFont("Helvetica", 10)
        text = body or ""
        for line in _wrap(text, 90):
            if y < inch:
                c.showPage()
                y = height - inch
            c.drawString(inch, y, line)
            y -= 0.16 * inch

    y -= 0.3 * inch
    if y < inch:
        c.showPage()
        y = height - inch
    c.setFont("Helvetica", 10)
    if note.signed_at:
        c.drawString(
            inch,
            y,
            f"Signed: {note.signed_at.astimezone(UTC).strftime('%Y-%m-%d %H:%M UTC')}",
        )
    else:
        c.drawString(inch, y, "Signature: _________________________")

    c.showPage()
    c.save()
    return buffer.getvalue()


def _wrap(text: str, width: int) -> list[str]:
    if not text:
        return [""]
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


async def get_soap_pdf_bytes(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    appointment_id: uuid.UUID,
    version: int,
) -> bytes:
    note = await get_soap_version(db, clinic_id, appointment_id, version)
    clinic_result = await db.execute(select(Clinic).where(Clinic.id == clinic_id))
    clinic = clinic_result.scalar_one()
    patient_result = await db.execute(select(Patient).where(Patient.id == note.patient_id))
    patient = patient_result.scalar_one()
    doctor_result = await db.execute(
        select(DoctorProfile, User)
        .join(User, User.id == DoctorProfile.user_id)
        .where(DoctorProfile.id == note.doctor_id)
    )
    row = doctor_result.one_or_none()
    doctor_name = row[1].full_name if row else "Doctor"
    return render_soap_pdf(clinic, patient, note, doctor_name)
