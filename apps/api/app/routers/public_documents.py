from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.patient_portal import (
    PatientPortalChartSummaryRead,
    PatientPortalDiagnosisRead,
    PatientPortalVitalRead,
)
from app.services.document_service import resolve_chart_share
from app.services.patient_portal_service import get_chart_summary

router = APIRouter(tags=["public-documents"])


@router.get("/public/referral-chart/{token}", response_model=PatientPortalChartSummaryRead)
async def get_public_referral_chart(
    token: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PatientPortalChartSummaryRead:
    patient = await resolve_chart_share(db, token)
    data = await get_chart_summary(db, patient)
    return PatientPortalChartSummaryRead(
        diagnoses=[PatientPortalDiagnosisRead(**d) for d in data["diagnoses"]],
        vitals=[PatientPortalVitalRead.model_validate(v) for v in data["vitals"]],
    )
