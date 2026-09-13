import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.soap_draft_service import stream_soap_draft_sse
from app.core.db import get_db
from app.core.deps import ClinicStaff
from app.core.security import get_active_clinic_membership, get_current_user
from app.data.specialty_templates import SPECIALTY_TEMPLATES
from app.models import ClinicMembership, User
from app.schemas.soap import (
    SoapDraftRequest,
    SoapNoteCreate,
    SoapNoteListResponse,
    SoapNoteRead,
    SpecialtyTemplateRead,
)
from app.services.ai_usage_service import assert_ai_usage_available
from app.services.appointment_service import get_appointment
from app.services.clinic_service import get_clinic
from app.services.clinical_access import assert_soap_read, assert_soap_write
from app.services.soap_service import (
    create_soap_version,
    get_soap_pdf_bytes,
    get_soap_version,
    list_soap_versions,
    sign_soap_version,
)

router = APIRouter(tags=["soap"])


async def _clinic_id(
    membership: Annotated[ClinicMembership, Depends(get_active_clinic_membership)],
) -> uuid.UUID:
    return membership.clinic_id


async def _enrich_notes(db: AsyncSession, notes: list) -> list[SoapNoteRead]:
    if not notes:
        return []
    user_ids = {n.created_by_user_id for n in notes}
    users = await db.execute(select(User).where(User.id.in_(user_ids)))
    name_map = {u.id: u.full_name for u in users.scalars()}
    out = []
    for n in notes:
        row = SoapNoteRead.model_validate(n)
        row.author_name = name_map.get(n.created_by_user_id)
        out.append(row)
    return out


@router.get("/specialty-templates", response_model=list[SpecialtyTemplateRead])
async def list_specialty_templates(
    membership: ClinicStaff,
) -> list[SpecialtyTemplateRead]:
    return [SpecialtyTemplateRead.model_validate(t) for t in SPECIALTY_TEMPLATES]


@router.post("/appointments/{appointment_id}/soap-draft")
async def post_soap_draft(
    appointment_id: uuid.UUID,
    data: SoapDraftRequest,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StreamingResponse:
    appt = await get_appointment(db, clinic_id, appointment_id)
    await assert_soap_write(db, membership, appt.doctor_id, user)
    await assert_ai_usage_available(db, clinic_id)
    return StreamingResponse(
        stream_soap_draft_sse(db, clinic_id, appointment_id, data.input_text, user, membership),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/appointments/{appointment_id}/soap-notes", response_model=SoapNoteRead)
async def post_soap_note(
    appointment_id: uuid.UUID,
    data: SoapNoteCreate,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SoapNoteRead:
    note = await create_soap_version(db, clinic_id, appointment_id, data, user, membership)
    enriched = await _enrich_notes(db, [note])
    return enriched[0]


@router.get("/appointments/{appointment_id}/soap-notes", response_model=SoapNoteListResponse)
async def get_soap_notes(
    appointment_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
    version: int | None = Query(default=None),
) -> SoapNoteListResponse:
    clinic = await get_clinic(db, clinic_id)
    await assert_soap_read(db, membership, clinic)
    if version is not None:
        note = await get_soap_version(db, clinic_id, appointment_id, version)
        enriched = await _enrich_notes(db, [note])
        return SoapNoteListResponse(items=enriched, latest_version=note.version_number)
    notes = await list_soap_versions(db, clinic_id, appointment_id)
    enriched = await _enrich_notes(db, notes)
    latest = notes[0].version_number if notes else None
    return SoapNoteListResponse(items=enriched, latest_version=latest)


@router.post(
    "/appointments/{appointment_id}/soap-notes/{version}/sign",
    response_model=SoapNoteRead,
)
async def post_sign_soap(
    appointment_id: uuid.UUID,
    version: int,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SoapNoteRead:
    note = await sign_soap_version(db, clinic_id, appointment_id, version, user, membership)
    enriched = await _enrich_notes(db, [note])
    return enriched[0]


@router.get("/appointments/{appointment_id}/soap-notes/{version}/pdf")
async def get_soap_pdf(
    appointment_id: uuid.UUID,
    version: int,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    clinic = await get_clinic(db, clinic_id)
    await assert_soap_read(db, membership, clinic)
    pdf_bytes = await get_soap_pdf_bytes(db, clinic_id, appointment_id, version)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="soap-{appointment_id}-v{version}.pdf"'},
    )
