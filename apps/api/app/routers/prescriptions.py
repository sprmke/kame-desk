import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.prescription_explain import explain_safety_flag
from app.core.db import get_db
from app.core.deps import ClinicStaff
from app.core.security import get_active_clinic_membership, get_current_user
from app.models import ClinicMembership, DoctorProfile, Prescription, User
from app.schemas.billing_assist import (
    PrescriptionFlagExplainRequest,
    PrescriptionFlagExplainResponse,
)
from app.schemas.prescription import (
    ConflictFlagRead,
    PrescriptionConflictCheck,
    PrescriptionConflictResponse,
    PrescriptionCreate,
    PrescriptionIssue,
    PrescriptionListResponse,
    PrescriptionRead,
    PrescriptionVoid,
)
from app.services.clinical_access import assert_prescription_read
from app.services.patient_service import get_patient
from app.services.prescription_safety import check_allergy_interaction_conflicts
from app.services.prescription_service import (
    create_prescription_draft,
    get_prescription_pdf_bytes,
    issue_prescription,
    list_patient_prescriptions,
    void_prescription,
)
from app.services.storage_service import create_presigned_download

router = APIRouter(tags=["prescriptions"])


async def _clinic_id(
    membership: Annotated[ClinicMembership, Depends(get_active_clinic_membership)],
) -> uuid.UUID:
    return membership.clinic_id


async def _enrich(
    db: AsyncSession,
    prescriptions: list[Prescription],
) -> list[PrescriptionRead]:
    if not prescriptions:
        return []
    doctor_ids = {p.doctor_id for p in prescriptions}
    doctors = await db.execute(
        select(DoctorProfile, User)
        .join(User, User.id == DoctorProfile.user_id)
        .where(DoctorProfile.id.in_(doctor_ids))
    )
    name_map = {d.id: u.full_name for d, u in doctors.all()}
    out: list[PrescriptionRead] = []
    for p in prescriptions:
        row = PrescriptionRead.model_validate(p)
        row.doctor_name = name_map.get(p.doctor_id)
        if p.pdf_object_key:
            row.pdf_download_url = create_presigned_download(p.pdf_object_key)
        out.append(row)
    return out


@router.post("/patients/{patient_id}/prescriptions", response_model=PrescriptionRead)
async def post_prescription(
    patient_id: uuid.UUID,
    data: PrescriptionCreate,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PrescriptionRead:
    rx = await create_prescription_draft(db, clinic_id, patient_id, data, user, membership)
    enriched = await _enrich(db, [rx])
    return enriched[0]


@router.post(
    "/patients/{patient_id}/prescription-conflicts",
    response_model=PrescriptionConflictResponse,
)
async def post_prescription_conflicts(
    patient_id: uuid.UUID,
    data: PrescriptionConflictCheck,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PrescriptionConflictResponse:
    await assert_prescription_read(membership)
    await get_patient(db, clinic_id, patient_id)
    flags = await check_allergy_interaction_conflicts(db, patient_id, data.drug_names)
    return PrescriptionConflictResponse(flags=[ConflictFlagRead.model_validate(f) for f in flags])


@router.post(
    "/patients/{patient_id}/prescription-flag/explain",
    response_model=PrescriptionFlagExplainResponse,
)
async def post_explain_prescription_flag(
    patient_id: uuid.UUID,
    data: PrescriptionFlagExplainRequest,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PrescriptionFlagExplainResponse:
    from app.services.ai_usage_service import assert_ai_usage_available, record_ai_usage

    if membership.role not in ("doctor", "owner"):
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="Prescription write not allowed")
    await get_patient(db, clinic_id, patient_id)
    await assert_ai_usage_available(db, clinic_id)
    explanation = await explain_safety_flag(data.flag.model_dump())
    await record_ai_usage(db, clinic_id)
    return PrescriptionFlagExplainResponse(explanation=explanation, flag=data.flag)


@router.get("/patients/{patient_id}/prescriptions", response_model=PrescriptionListResponse)
async def get_patient_prescriptions(
    patient_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PrescriptionListResponse:
    await assert_prescription_read(membership)
    items = await list_patient_prescriptions(db, clinic_id, patient_id)
    enriched = await _enrich(db, items)
    return PrescriptionListResponse(items=enriched, total=len(enriched))


@router.post("/prescriptions/{prescription_id}/issue", response_model=PrescriptionRead)
async def post_issue_prescription(
    prescription_id: uuid.UUID,
    data: PrescriptionIssue,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PrescriptionRead:
    rx = await issue_prescription(
        db,
        clinic_id,
        prescription_id,
        user,
        membership,
        data.override_reason,
    )
    enriched = await _enrich(db, [rx])
    return enriched[0]


@router.post("/prescriptions/{prescription_id}/void", response_model=PrescriptionRead)
async def post_void_prescription(
    prescription_id: uuid.UUID,
    data: PrescriptionVoid,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PrescriptionRead:
    rx = await void_prescription(db, clinic_id, prescription_id, user, membership, data.reason)
    enriched = await _enrich(db, [rx])
    return enriched[0]


@router.get("/prescriptions/{prescription_id}/pdf")
async def get_prescription_pdf(
    prescription_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    await assert_prescription_read(membership)
    pdf_bytes, rx = await get_prescription_pdf_bytes(db, clinic_id, prescription_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="prescription-{prescription_id}.pdf"'},
    )
