import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    ActivityLog,
    Appointment,
    Clinic,
    ClinicMembership,
    DocumentTemplate,
    GeneratedDocument,
    Patient,
    PatientFile,
    User,
)
from app.schemas.document import (
    DocumentTemplateCreate,
    DocumentTemplateUpdate,
    GeneratedDocumentCreate,
    GeneratedDocumentUpdate,
)
from app.services import document_pdf
from app.services.clinical_access import get_doctor_profile_for_user
from app.services.document_access import assert_document_write, assert_template_admin
from app.services.patient_service import get_patient
from app.services.storage_service import upload_object_bytes
from app.services.template_renderer import render_template, validate_template_body

LETTER_TYPES = (
    "medical_certificate",
    "referral_letter",
    "lab_request",
    "confinement_certificate",
    "custom",
)


async def list_letter_templates(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    include_inactive: bool = False,
) -> list[DocumentTemplate]:
    query = select(DocumentTemplate).where(
        DocumentTemplate.template_type.in_(LETTER_TYPES),
        or_(DocumentTemplate.clinic_id == clinic_id, DocumentTemplate.clinic_id.is_(None)),
    )
    if not include_inactive:
        query = query.where(DocumentTemplate.is_active.is_(True))
    result = await db.execute(query.order_by(DocumentTemplate.name))
    return list(result.scalars().all())


async def create_letter_template(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    data: DocumentTemplateCreate,
    actor: User,
    membership: ClinicMembership,
) -> DocumentTemplate:
    assert_template_admin(membership)
    try:
        validate_template_body(data.body_template)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    existing = await db.execute(
        select(DocumentTemplate).where(
            DocumentTemplate.clinic_id == clinic_id,
            DocumentTemplate.template_key == data.template_key,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Template key already exists")
    row = DocumentTemplate(
        clinic_id=clinic_id,
        template_key=data.template_key,
        name=data.name,
        template_type=data.template_type,
        schema_version=1,
        body={},
        body_template=data.body_template,
        is_active=data.is_active,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(row)
    await db.flush()
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor.id,
            actor_type="user",
            action="document_template.created",
            target_type="document_template",
            target_id=str(row.id),
            summary=f"Template created ({data.template_key})",
        )
    )
    await db.commit()
    await db.refresh(row)
    return row


async def update_letter_template(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    template_id: uuid.UUID,
    data: DocumentTemplateUpdate,
    actor: User,
    membership: ClinicMembership,
) -> DocumentTemplate:
    assert_template_admin(membership)
    row = await _get_clinic_template(db, clinic_id, template_id)
    if data.body_template is not None:
        try:
            validate_template_body(data.body_template)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        row.body_template = data.body_template
    if data.name is not None:
        row.name = data.name
    if data.is_active is not None:
        row.is_active = data.is_active
    row.updated_at = datetime.now(UTC)
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor.id,
            actor_type="user",
            action="document_template.updated",
            target_type="document_template",
            target_id=str(row.id),
            summary="Template updated",
        )
    )
    await db.commit()
    await db.refresh(row)
    return row


async def _get_clinic_template(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    template_id: uuid.UUID,
) -> DocumentTemplate:
    result = await db.execute(
        select(DocumentTemplate).where(
            DocumentTemplate.id == template_id,
            DocumentTemplate.clinic_id == clinic_id,
            DocumentTemplate.template_type.in_(LETTER_TYPES),
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return row


async def _build_context(
    db: AsyncSession,
    clinic: Clinic,
    patient: Patient,
    user: User,
    membership: ClinicMembership,
    appointment_id: uuid.UUID | None,
    extra: dict[str, str],
) -> dict[str, Any]:
    doctor = await get_doctor_profile_for_user(db, user, membership.clinic_id)
    doctor_name = user.full_name
    specialty = ""
    prc = ""
    if doctor:
        specialty = doctor.specialty or ""
        prc = doctor.prc_license_number or ""

    appt_reason = ""
    if appointment_id:
        appt = await db.get(Appointment, appointment_id)
        if appt and appt.clinic_id == clinic.id:
            appt_reason = appt.reason_for_visit or ""

    context: dict[str, Any] = {
        "patient": {
            "full_name": patient.full_name,
            "birthdate": str(patient.birthdate) if patient.birthdate else "",
            "contact_number": patient.contact_number or "",
            "address": patient.address or "",
        },
        "clinic": {
            "name": clinic.name,
            "address": clinic.address or "",
            "contact_phone": clinic.contact_phone or "",
        },
        "doctor": {
            "full_name": doctor_name,
            "specialty": specialty,
            "prc_license_number": prc,
        },
        "visit": {
            "reason_for_visit": appt_reason,
            "date": datetime.now(UTC).astimezone().strftime("%Y-%m-%d"),
        },
        "extra": extra,
    }
    return context


async def create_document_draft(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    patient_id: uuid.UUID,
    data: GeneratedDocumentCreate,
    actor: User,
    membership: ClinicMembership,
    *,
    actor_type: str = "user",
) -> GeneratedDocument:
    assert_document_write(membership)
    patient = await get_patient(db, clinic_id, patient_id)
    clinic = await db.get(Clinic, clinic_id)
    if clinic is None:
        raise HTTPException(status_code=404, detail="Clinic not found")

    template = await db.get(DocumentTemplate, data.template_id)
    if template is None or template.template_type not in LETTER_TYPES:
        raise HTTPException(status_code=404, detail="Template not found")
    if template.clinic_id not in (None, clinic_id):
        raise HTTPException(status_code=404, detail="Template not found")
    if not template.is_active or not template.body_template:
        raise HTTPException(status_code=400, detail="Template not available")

    if data.appointment_id:
        appt = await db.get(Appointment, data.appointment_id)
        if appt is None or appt.patient_id != patient_id or appt.clinic_id != clinic_id:
            raise HTTPException(status_code=400, detail="Invalid appointment")

    context = await _build_context(
        db,
        clinic,
        patient,
        actor,
        membership,
        data.appointment_id,
        data.extra_context,
    )
    preview = render_template(template.body_template, context)

    doc = GeneratedDocument(
        clinic_id=clinic_id,
        patient_id=patient_id,
        appointment_id=data.appointment_id,
        template_id=template.id,
        document_type=template.template_type,
        status="draft",
        preview_content=preview,
        created_by_user_id=actor.id,
        referral_recipient=data.referral_recipient,
        referral_status="draft" if template.template_type == "referral_letter" else None,
    )
    db.add(doc)
    await db.flush()
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor.id,
            actor_type=actor_type,
            action="document.draft_created",
            target_type="generated_document",
            target_id=str(doc.id),
            summary=f"Document draft ({template.name})",
        )
    )
    await db.commit()
    await db.refresh(doc)
    return doc


async def _assert_issuer_completeness(
    db: AsyncSession,
    actor: User,
    clinic_id: uuid.UUID,
) -> None:
    doctor = await get_doctor_profile_for_user(db, actor, clinic_id)
    if doctor is None:
        raise HTTPException(
            status_code=400,
            detail="Doctor profile required. Update doctor profile in Settings.",
        )
    if not doctor.prc_license_number:
        raise HTTPException(
            status_code=400,
            detail="PRC license required. Update doctor profile in Settings.",
        )
    if not doctor.signature_image_key:
        raise HTTPException(
            status_code=400,
            detail="Signature required. Upload a signature in Settings.",
        )


async def issue_document(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    document_id: uuid.UUID,
    actor: User,
    membership: ClinicMembership,
    *,
    actor_type: str = "user",
) -> GeneratedDocument:
    assert_document_write(membership)
    await _assert_issuer_completeness(db, actor, clinic_id)
    doc = await _get_document(db, clinic_id, document_id)
    if doc.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft documents can be issued")

    patient = await get_patient(db, clinic_id, doc.patient_id)
    clinic = await db.get(Clinic, clinic_id)
    if clinic is None:
        raise HTTPException(status_code=404, detail="Clinic not found")

    template = await db.get(DocumentTemplate, doc.template_id)
    title = template.name if template else doc.document_type

    doc.final_content_snapshot = doc.preview_content
    pdf_bytes = document_pdf.render_document_pdf(
        clinic.name,
        title,
        doc.final_content_snapshot,
        signed=True,
        brand_color=clinic.brand_color,
    )
    object_key = f"documents/{clinic_id}/{doc.id}.pdf"
    upload_object_bytes(object_key, pdf_bytes, "application/pdf")
    doc.pdf_object_key = object_key

    file_row = PatientFile(
        patient_id=patient.id,
        clinic_id=clinic_id,
        r2_key=object_key,
        file_type="clinical_document",
        description=f"{title} (issued)",
        uploaded_by_user_id=actor.id,
        visit_id=doc.appointment_id,
    )
    db.add(file_row)
    await db.flush()

    doc.patient_file_id = file_row.id
    doc.status = "issued"
    doc.issued_by_user_id = actor.id
    doc.issued_at = datetime.now(UTC)

    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor.id,
            actor_type=actor_type,
            action="document.issued",
            target_type="generated_document",
            target_id=str(doc.id),
            summary=f"Document issued ({title})",
        )
    )
    await db.commit()
    await db.refresh(doc)
    from app.services.notification_service import notify_document_issued

    await notify_document_issued(
        db,
        clinic_id=clinic_id,
        document_id=doc.id,
        patient_id=patient.id,
        actor_user_id=actor.id,
    )
    return doc


async def list_patient_documents(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    patient_id: uuid.UUID,
) -> list[GeneratedDocument]:
    await get_patient(db, clinic_id, patient_id)
    result = await db.execute(
        select(GeneratedDocument)
        .where(
            GeneratedDocument.patient_id == patient_id,
            GeneratedDocument.clinic_id == clinic_id,
        )
        .order_by(GeneratedDocument.created_at.desc())
    )
    return list(result.scalars().all())


async def _get_document(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    document_id: uuid.UUID,
) -> GeneratedDocument:
    result = await db.execute(
        select(GeneratedDocument).where(
            GeneratedDocument.id == document_id,
            GeneratedDocument.clinic_id == clinic_id,
        )
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


async def get_document_pdf_bytes(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    document_id: uuid.UUID,
) -> tuple[bytes, GeneratedDocument]:
    doc = await _get_document(db, clinic_id, document_id)
    if doc.status != "issued" or not doc.final_content_snapshot:
        raise HTTPException(status_code=400, detail="Document not issued")
    clinic = await db.get(Clinic, clinic_id)
    template = await db.get(DocumentTemplate, doc.template_id)
    title = template.name if template else doc.document_type
    if clinic is None:
        raise HTTPException(status_code=404, detail="Clinic not found")
    return (
        document_pdf.render_document_pdf(
            clinic.name,
            title,
            doc.final_content_snapshot,
            signed=True,
            brand_color=clinic.brand_color,
        ),
        doc,
    )


async def update_generated_document(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    document_id: uuid.UUID,
    data: GeneratedDocumentUpdate,
    actor_id: uuid.UUID,
) -> GeneratedDocument:
    doc = await _get_document(db, clinic_id, document_id)
    payload = data.model_dump(exclude_unset=True)
    if "referral_recipient" in payload:
        doc.referral_recipient = payload["referral_recipient"]
    if "referral_status" in payload:
        doc.referral_status = payload["referral_status"]
    if "referral_outcome" in payload:
        doc.referral_outcome = payload["referral_outcome"]
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor_id,
            actor_type="user",
            action="document.referral_updated",
            target_type="generated_document",
            target_id=str(doc.id),
            summary="Referral tracking updated",
        )
    )
    await db.commit()
    await db.refresh(doc)
    return doc


CHART_SHARE_TTL = timedelta(days=7)


async def create_chart_share(
    db: AsyncSession, clinic_id: uuid.UUID, document_id: uuid.UUID, actor_id: uuid.UUID
) -> tuple[str, datetime]:
    """Create (or rotate) a scoped, expiring share link for a referral
    document's chart-summary snapshot. No recipient account required."""
    doc = await _get_document(db, clinic_id, document_id)
    if doc.document_type != "referral_letter":
        raise HTTPException(status_code=400, detail="Only referral letters can share a chart")

    raw = secrets.token_urlsafe(32)
    doc.chart_share_token_hash = hashlib.sha256(raw.encode()).hexdigest()
    doc.chart_share_expires_at = datetime.now(UTC) + CHART_SHARE_TTL
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor_id,
            actor_type="user",
            action="referral.chart_shared",
            target_type="generated_document",
            target_id=str(doc.id),
            summary="Referral chart-summary share link created",
        )
    )
    await db.commit()
    return raw, doc.chart_share_expires_at


async def resolve_chart_share(db: AsyncSession, raw_token: str) -> Patient:
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    result = await db.execute(
        select(GeneratedDocument).where(GeneratedDocument.chart_share_token_hash == token_hash)
    )
    doc = result.scalar_one_or_none()
    if (
        doc is None
        or doc.chart_share_expires_at is None
        or doc.chart_share_expires_at < datetime.now(UTC)
    ):
        raise HTTPException(status_code=404, detail="Share link is invalid or expired")
    patient = await db.get(Patient, doc.patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Share link is invalid or expired")
    return patient
