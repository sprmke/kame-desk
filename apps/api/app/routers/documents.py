import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.deps import ClinicStaff
from app.core.security import get_active_clinic_membership, get_current_user
from app.models import ClinicMembership, DocumentTemplate, GeneratedDocument, User
from app.schemas.document import (
    ChartShareRead,
    DocumentTemplateCreate,
    DocumentTemplatePreviewRead,
    DocumentTemplatePreviewRequest,
    DocumentTemplateRead,
    DocumentTemplateUpdate,
    GeneratedDocumentCreate,
    GeneratedDocumentListResponse,
    GeneratedDocumentRead,
    GeneratedDocumentUpdate,
)
from app.services.document_access import assert_document_read
from app.services.document_service import (
    create_chart_share,
    create_document_draft,
    create_letter_template,
    get_document_pdf_bytes,
    issue_document,
    list_letter_templates,
    list_patient_documents,
    update_generated_document,
    update_letter_template,
)
from app.services.template_renderer import (
    SAMPLE_TEMPLATE_CONTEXT,
    TEMPLATE_PLACEHOLDERS,
    render_template,
)

router = APIRouter(tags=["documents"])


async def _clinic_id(
    membership: Annotated[ClinicMembership, Depends(get_active_clinic_membership)],
) -> uuid.UUID:
    return membership.clinic_id


def _template_read(row: DocumentTemplate) -> DocumentTemplateRead:
    return DocumentTemplateRead(
        id=row.id,
        clinic_id=row.clinic_id,
        template_key=row.template_key,
        name=row.name,
        template_type=row.template_type,
        body_template=row.body_template,
        is_active=row.is_active,
    )


async def _doc_read(db: AsyncSession, doc: GeneratedDocument) -> GeneratedDocumentRead:
    template = await db.get(DocumentTemplate, doc.template_id)
    row = GeneratedDocumentRead.model_validate(doc)
    row.template_name = template.name if template else None
    return row


@router.get("/clinics/{clinic_id}/document-templates", response_model=list[DocumentTemplateRead])
async def get_document_templates(
    clinic_id: uuid.UUID,
    membership: Annotated[ClinicMembership, Depends(get_active_clinic_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[DocumentTemplateRead]:
    if membership.clinic_id != clinic_id:
        raise HTTPException(status_code=403, detail="Clinic mismatch")
    assert_document_read(membership)
    rows = await list_letter_templates(db, clinic_id, include_inactive=True)
    return [_template_read(r) for r in rows if r.clinic_id == clinic_id]


@router.get(
    "/clinics/{clinic_id}/document-templates/placeholders",
    response_model=list[str],
)
async def get_template_placeholders(
    clinic_id: uuid.UUID,
    membership: Annotated[ClinicMembership, Depends(get_active_clinic_membership)],
) -> list[str]:
    if membership.clinic_id != clinic_id:
        raise HTTPException(status_code=403, detail="Clinic mismatch")
    assert_document_read(membership)
    return list(TEMPLATE_PLACEHOLDERS)


@router.post(
    "/clinics/{clinic_id}/document-templates/preview",
    response_model=DocumentTemplatePreviewRead,
)
async def preview_document_template(
    clinic_id: uuid.UUID,
    data: DocumentTemplatePreviewRequest,
    membership: Annotated[ClinicMembership, Depends(get_active_clinic_membership)],
) -> DocumentTemplatePreviewRead:
    if membership.clinic_id != clinic_id:
        raise HTTPException(status_code=403, detail="Clinic mismatch")
    assert_document_read(membership)
    try:
        preview = render_template(data.body_template, SAMPLE_TEMPLATE_CONTEXT)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return DocumentTemplatePreviewRead(
        placeholders=list(TEMPLATE_PLACEHOLDERS),
        preview=preview,
    )


@router.post("/clinics/{clinic_id}/document-templates", response_model=DocumentTemplateRead)
async def post_document_template(
    clinic_id: uuid.UUID,
    data: DocumentTemplateCreate,
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DocumentTemplateRead:
    if membership.clinic_id != clinic_id:
        raise HTTPException(status_code=403, detail="Clinic mismatch")
    row = await create_letter_template(db, clinic_id, data, user, membership)
    return _template_read(row)


@router.patch(
    "/clinics/{clinic_id}/document-templates/{template_id}",
    response_model=DocumentTemplateRead,
)
async def patch_document_template(
    clinic_id: uuid.UUID,
    template_id: uuid.UUID,
    data: DocumentTemplateUpdate,
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DocumentTemplateRead:
    if membership.clinic_id != clinic_id:
        raise HTTPException(status_code=403, detail="Clinic mismatch")
    row = await update_letter_template(db, clinic_id, template_id, data, user, membership)
    return _template_read(row)


@router.post("/patients/{patient_id}/documents", response_model=GeneratedDocumentRead)
async def post_patient_document(
    patient_id: uuid.UUID,
    data: GeneratedDocumentCreate,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GeneratedDocumentRead:
    doc = await create_document_draft(db, clinic_id, patient_id, data, user, membership)
    return await _doc_read(db, doc)


@router.get("/patients/{patient_id}/documents", response_model=GeneratedDocumentListResponse)
async def get_patient_documents(
    patient_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GeneratedDocumentListResponse:
    assert_document_read(membership)
    items = await list_patient_documents(db, clinic_id, patient_id)
    enriched = [await _doc_read(db, d) for d in items]
    return GeneratedDocumentListResponse(items=enriched, total=len(enriched))


@router.patch("/documents/{document_id}", response_model=GeneratedDocumentRead)
async def patch_generated_document(
    document_id: uuid.UUID,
    data: GeneratedDocumentUpdate,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GeneratedDocumentRead:
    doc = await update_generated_document(db, clinic_id, document_id, data, user.id)
    return await _doc_read(db, doc)


@router.post("/documents/{document_id}/issue", response_model=GeneratedDocumentRead)
async def post_issue_document(
    document_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GeneratedDocumentRead:
    doc = await issue_document(db, clinic_id, document_id, user, membership)
    return await _doc_read(db, doc)


@router.post("/documents/{document_id}/chart-share", response_model=ChartShareRead)
async def post_chart_share(
    document_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChartShareRead:
    assert_document_read(membership)
    raw_token, expires_at = await create_chart_share(db, clinic_id, document_id, user.id)
    return ChartShareRead(
        share_url=f"{settings.web_base_url}/referral-chart/{raw_token}", expires_at=expires_at
    )


@router.get("/documents/{document_id}/pdf")
async def get_document_pdf(
    document_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    assert_document_read(membership)
    pdf_bytes, doc = await get_document_pdf_bytes(db, clinic_id, document_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="document-{document_id}.pdf"'},
    )
