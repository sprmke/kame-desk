from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.patient_survey import PatientSurveyResponseRead
from app.services.growth_service import respond_to_nps

router = APIRouter(tags=["public-nps"])


class NpsRespond(BaseModel):
    score: int = Field(ge=0, le=10)
    comment: str | None = Field(default=None, max_length=2000)


@router.post("/public/nps/{token}/respond", response_model=PatientSurveyResponseRead)
async def post_nps_respond(
    token: str,
    data: NpsRespond,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PatientSurveyResponseRead:
    survey = await respond_to_nps(db, token, data.score, data.comment)
    return PatientSurveyResponseRead.model_validate(survey)
