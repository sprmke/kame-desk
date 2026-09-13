import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.rate_limit import enforce_public_rate_limit
from app.core.security import get_current_patient
from app.models import Patient
from app.schemas.patient_portal import (
    PatientPortalChartSummaryRead,
    PatientPortalDiagnosisRead,
    PatientPortalDocumentDownloadRead,
    PatientPortalDocumentRead,
    PatientPortalInvoiceListResponse,
    PatientPortalLoginRequest,
    PatientPortalLoginRequestResponse,
    PatientPortalMeRead,
    PatientPortalSessionRead,
    PatientPortalVerifyRequest,
    PatientPortalVisitRead,
    PatientPortalVitalRead,
)
from app.services import patient_portal_service

router = APIRouter(prefix="/patient-portal", tags=["patient-portal"])


@router.post("/login/request", response_model=PatientPortalLoginRequestResponse)
async def post_login_request(
    data: PatientPortalLoginRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PatientPortalLoginRequestResponse:
    enforce_public_rate_limit(request, data.clinic_slug)
    await patient_portal_service.request_login_link(db, data.clinic_slug, data.identifier)
    return PatientPortalLoginRequestResponse()


@router.post("/login/verify", response_model=PatientPortalSessionRead)
async def post_login_verify(
    data: PatientPortalVerifyRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PatientPortalSessionRead:
    access_token, patient_id, clinic_id = await patient_portal_service.verify_login_link(
        db, data.token
    )
    return PatientPortalSessionRead(
        access_token=access_token,
        expires_in_minutes=settings.patient_access_token_expire_minutes,
        patient_id=patient_id,
        clinic_id=clinic_id,
    )


@router.get("/me", response_model=PatientPortalMeRead)
async def get_me(
    patient: Annotated[Patient, Depends(get_current_patient)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PatientPortalMeRead:
    data = await patient_portal_service.get_me(db, patient)
    return PatientPortalMeRead(**data)


@router.get("/visits", response_model=list[PatientPortalVisitRead])
async def get_visits(
    patient: Annotated[Patient, Depends(get_current_patient)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[PatientPortalVisitRead]:
    visits = await patient_portal_service.list_visits(db, patient)
    return [PatientPortalVisitRead(**v) for v in visits]


@router.get("/chart-summary", response_model=PatientPortalChartSummaryRead)
async def get_chart_summary(
    patient: Annotated[Patient, Depends(get_current_patient)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PatientPortalChartSummaryRead:
    data = await patient_portal_service.get_chart_summary(db, patient)
    return PatientPortalChartSummaryRead(
        diagnoses=[PatientPortalDiagnosisRead(**d) for d in data["diagnoses"]],
        vitals=[PatientPortalVitalRead.model_validate(v) for v in data["vitals"]],
    )


@router.get("/invoices", response_model=PatientPortalInvoiceListResponse)
async def get_invoices(
    patient: Annotated[Patient, Depends(get_current_patient)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PatientPortalInvoiceListResponse:
    return PatientPortalInvoiceListResponse.model_validate(
        await patient_portal_service.list_invoices(db, patient)
    )


@router.get("/documents", response_model=list[PatientPortalDocumentRead])
async def get_documents(
    patient: Annotated[Patient, Depends(get_current_patient)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[PatientPortalDocumentRead]:
    files = await patient_portal_service.list_documents(db, patient)
    return [PatientPortalDocumentRead.model_validate(f) for f in files]


@router.get("/documents/{file_id}/download", response_model=PatientPortalDocumentDownloadRead)
async def get_document_download(
    file_id: uuid.UUID,
    patient: Annotated[Patient, Depends(get_current_patient)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PatientPortalDocumentDownloadRead:
    url = await patient_portal_service.get_document_download(db, patient, file_id)
    return PatientPortalDocumentDownloadRead(download_url=url)
