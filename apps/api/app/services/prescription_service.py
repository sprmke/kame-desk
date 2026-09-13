import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    ActivityLog,
    Clinic,
    Prescription,
    PrescriptionItem,
    User,
)
from app.schemas.prescription import PrescriptionCreate
from app.services import prescription_pdf
from app.services.clinical_access import assert_prescription_write
from app.services.patient_service import get_patient
from app.services.prescription_safety import check_allergy_interaction_conflicts
from app.services.storage_service import upload_object_bytes


async def create_prescription_draft(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    patient_id: uuid.UUID,
    data: PrescriptionCreate,
    actor: User,
    membership,
    *,
    actor_type: str = "user",
) -> Prescription:
    doctor = await assert_prescription_write(db, membership, actor)
    await get_patient(db, clinic_id, patient_id)

    rx = Prescription(
        patient_id=patient_id,
        doctor_id=doctor.id,
        clinic_id=clinic_id,
        appointment_id=data.appointment_id,
        status="draft",
        notes=data.notes,
        created_by_user_id=actor.id,
    )
    db.add(rx)
    await db.flush()

    for idx, item in enumerate(data.items):
        db.add(
            PrescriptionItem(
                prescription_id=rx.id,
                drug_name=item.drug_name,
                generic_name=item.generic_name,
                dosage=item.dosage,
                form=item.form,
                frequency=item.frequency,
                duration=item.duration,
                quantity=item.quantity,
                special_instructions=item.special_instructions,
                sort_order=idx,
            )
        )

    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor.id,
            actor_type=actor_type,
            action="prescription.draft_created",
            target_type="prescription",
            target_id=str(rx.id),
            summary="Prescription draft created",
        )
    )
    await db.commit()
    return await get_prescription(db, clinic_id, rx.id)


async def get_prescription(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    prescription_id: uuid.UUID,
) -> Prescription:
    result = await db.execute(
        select(Prescription)
        .options(selectinload(Prescription.items))
        .where(Prescription.id == prescription_id, Prescription.clinic_id == clinic_id)
    )
    rx = result.scalar_one_or_none()
    if rx is None:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return rx


async def list_patient_prescriptions(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    patient_id: uuid.UUID,
) -> list[Prescription]:
    await get_patient(db, clinic_id, patient_id)
    result = await db.execute(
        select(Prescription)
        .options(selectinload(Prescription.items))
        .where(Prescription.patient_id == patient_id, Prescription.clinic_id == clinic_id)
        .order_by(Prescription.created_at.desc())
    )
    return list(result.scalars().all())


async def issue_prescription(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    prescription_id: uuid.UUID,
    actor: User,
    membership,
    override_reason: str | None,
) -> Prescription:
    doctor = await assert_prescription_write(db, membership, actor)
    rx = await get_prescription(db, clinic_id, prescription_id)
    if rx.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft prescriptions can be issued")
    if rx.doctor_id != doctor.id:
        raise HTTPException(status_code=403, detail="Not the prescribing doctor")

    if not doctor.prc_license_number:
        raise HTTPException(
            status_code=400,
            detail="PRC license required. Update doctor profile in Settings.",
        )

    drug_names = [item.drug_name for item in rx.items]
    flags = await check_allergy_interaction_conflicts(db, rx.patient_id, drug_names)
    if flags and not (override_reason and override_reason.strip()):
        raise HTTPException(
            status_code=409,
            detail={"message": "Safety flags require override reason", "flags": flags},
        )

    clinic_result = await db.execute(select(Clinic).where(Clinic.id == clinic_id))
    clinic = clinic_result.scalar_one()
    patient = await get_patient(db, clinic_id, rx.patient_id)
    user_result = await db.execute(select(User).where(User.id == doctor.user_id))
    doctor_user = user_result.scalar_one()

    pdf_bytes = prescription_pdf.render_prescription_pdf(
        clinic=clinic,
        patient=patient,
        doctor=doctor,
        doctor_name=doctor_user.full_name,
        prescription=rx,
        override_reason=override_reason.strip() if override_reason else None,
        conflict_flags=flags or None,
    )
    object_key = f"clinics/{clinic_id}/prescriptions/{rx.id}.pdf"
    upload_object_bytes(object_key, pdf_bytes, "application/pdf")

    now = datetime.now(UTC)
    rx.status = "issued"
    rx.issued_at = now
    rx.pdf_object_key = object_key
    rx.override_reason = override_reason.strip() if override_reason else None
    rx.conflict_flags = flags or None

    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor.id,
            actor_type="user",
            action="prescription.issued",
            target_type="prescription",
            target_id=str(rx.id),
            summary="Prescription issued",
            metadata_={
                "override_reason": rx.override_reason,
                "flag_count": len(flags),
            },
        )
    )
    await db.commit()
    await db.refresh(rx)
    from app.services.notification_service import notify_prescription_issued

    await notify_prescription_issued(
        db,
        clinic_id=clinic_id,
        prescription_id=rx.id,
        patient_id=rx.patient_id,
        actor_user_id=actor.id,
    )
    return rx


async def void_prescription(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    prescription_id: uuid.UUID,
    actor: User,
    membership,
    reason: str,
) -> Prescription:
    await assert_prescription_write(db, membership, actor)
    rx = await get_prescription(db, clinic_id, prescription_id)
    if rx.status != "issued":
        raise HTTPException(status_code=400, detail="Only issued prescriptions can be voided")

    rx.status = "voided"
    rx.voided_at = datetime.now(UTC)
    rx.void_reason = reason.strip()

    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor.id,
            actor_type="user",
            action="prescription.voided",
            target_type="prescription",
            target_id=str(rx.id),
            summary="Prescription voided",
            metadata_={"reason": rx.void_reason},
        )
    )
    await db.commit()
    await db.refresh(rx)
    return rx


async def get_prescription_pdf_bytes(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    prescription_id: uuid.UUID,
) -> tuple[bytes, Prescription]:
    rx = await get_prescription(db, clinic_id, prescription_id)
    if not rx.pdf_object_key:
        raise HTTPException(status_code=404, detail="PDF not available")

    from app.core.config import settings
    from app.services.storage_service import _client

    client = _client()
    obj = client.get_object(Bucket=settings.s3_bucket, Key=rx.pdf_object_key)
    return obj["Body"].read(), rx
