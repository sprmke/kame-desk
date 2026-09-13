import uuid
from datetime import date, timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import OwnerAdmin
from app.core.security import require_clinic_role
from app.models import ClinicMembership
from app.services.growth_service import get_nps_report
from app.services.report_service import (
    get_appointment_report,
    get_patient_growth_report,
    get_revenue_report,
    get_top_diagnoses_report,
    report_to_csv,
)

router = APIRouter(prefix="/reports", tags=["reports"])

OwnerOrDoctor = Annotated[
    ClinicMembership,
    Depends(require_clinic_role("owner", "doctor")),
]

ReportKey = Literal["appointments", "revenue", "patient-growth", "top-diagnoses"]


class ReportSeriesRow(BaseModel):
    period: str | None = None
    doctor_id: str | None = None
    service_type: str | None = None
    diagnosis: str | None = None
    booked: int | None = None
    completed: int | None = None
    no_show: int | None = None
    cancelled: int | None = None
    amount: str | None = None
    new_patients: int | None = None
    returning_patients: int | None = None
    visit_count: int | None = None


class ReportResponse(BaseModel):
    series: list[dict]
    from_date: str
    to_date: str
    totals: dict[str, str] | None = None


def _default_range() -> tuple[date, date]:
    to_d = date.today()
    return to_d - timedelta(days=30), to_d


def _validate_group_by(group_by: str, allowed: tuple[str, ...]) -> None:
    if group_by not in allowed:
        raise HTTPException(status_code=400, detail=f"group_by must be one of {allowed}")


@router.get("/appointments", response_model=ReportResponse)
async def report_appointments(
    membership: OwnerAdmin,
    db: Annotated[AsyncSession, Depends(get_db)],
    from_date: date | None = None,
    to_date: date | None = None,
    group_by: str = Query(default="day"),
    doctor_id: uuid.UUID | None = None,
) -> ReportResponse:
    _validate_group_by(group_by, ("day", "week", "month", "doctor"))
    start, end = _default_range()
    if from_date:
        start = from_date
    if to_date:
        end = to_date
    data = await get_appointment_report(
        db,
        membership.clinic_id,
        from_date=start,
        to_date=end,
        group_by=group_by,
        doctor_id=doctor_id,
    )
    return ReportResponse(**data)


@router.get("/revenue", response_model=ReportResponse)
async def report_revenue(
    membership: OwnerAdmin,
    db: Annotated[AsyncSession, Depends(get_db)],
    from_date: date | None = None,
    to_date: date | None = None,
    group_by: str = Query(default="day"),
    doctor_id: uuid.UUID | None = None,
) -> ReportResponse:
    _validate_group_by(group_by, ("day", "week", "month", "doctor", "service_type"))
    start, end = _default_range()
    if from_date:
        start = from_date
    if to_date:
        end = to_date
    data = await get_revenue_report(
        db,
        membership.clinic_id,
        from_date=start,
        to_date=end,
        group_by=group_by,
        doctor_id=doctor_id,
    )
    return ReportResponse(**data)


@router.get("/patient-growth", response_model=ReportResponse)
async def report_patient_growth(
    membership: OwnerAdmin,
    db: Annotated[AsyncSession, Depends(get_db)],
    from_date: date | None = None,
    to_date: date | None = None,
    group_by: str = Query(default="month"),
) -> ReportResponse:
    _validate_group_by(group_by, ("day", "week", "month"))
    start, end = _default_range()
    if from_date:
        start = from_date
    if to_date:
        end = to_date
    data = await get_patient_growth_report(
        db,
        membership.clinic_id,
        from_date=start,
        to_date=end,
        group_by=group_by,
    )
    return ReportResponse(**data)


@router.get("/nps")
async def report_nps(
    membership: OwnerAdmin,
    db: Annotated[AsyncSession, Depends(get_db)],
    from_date: date | None = None,
    to_date: date | None = None,
) -> dict:
    start, end = _default_range()
    if from_date:
        start = from_date
    if to_date:
        end = to_date
    return await get_nps_report(db, membership.clinic_id, from_date=start, to_date=end)


@router.get("/top-diagnoses", response_model=ReportResponse)
async def report_top_diagnoses(
    membership: OwnerOrDoctor,
    db: Annotated[AsyncSession, Depends(get_db)],
    from_date: date | None = None,
    to_date: date | None = None,
    limit: int = Query(default=20, ge=1, le=100),
) -> ReportResponse:
    start, end = _default_range()
    if from_date:
        start = from_date
    if to_date:
        end = to_date
    data = await get_top_diagnoses_report(
        db,
        membership.clinic_id,
        from_date=start,
        to_date=end,
        limit=limit,
    )
    return ReportResponse(**data)


@router.get("/{report_key}/export.csv")
async def export_report_csv(
    report_key: ReportKey,
    membership: Annotated[
        ClinicMembership, Depends(require_clinic_role("owner", "admin", "doctor"))
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
    from_date: date | None = None,
    to_date: date | None = None,
    group_by: str = Query(default="day"),
) -> PlainTextResponse:
    if report_key == "top-diagnoses":
        if membership.role not in ("owner", "doctor"):
            raise HTTPException(status_code=403, detail="Not allowed")
    elif membership.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Not allowed")

    start, end = _default_range()
    if from_date:
        start = from_date
    if to_date:
        end = to_date

    if report_key == "appointments":
        payload = await get_appointment_report(
            db, membership.clinic_id, from_date=start, to_date=end, group_by=group_by
        )
    elif report_key == "revenue":
        payload = await get_revenue_report(
            db, membership.clinic_id, from_date=start, to_date=end, group_by=group_by
        )
    elif report_key == "patient-growth":
        payload = await get_patient_growth_report(
            db, membership.clinic_id, from_date=start, to_date=end, group_by=group_by
        )
    else:
        payload = await get_top_diagnoses_report(
            db, membership.clinic_id, from_date=start, to_date=end
        )

    csv_body = report_to_csv(report_key, payload)
    return PlainTextResponse(
        content=csv_body,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{report_key}.csv"'},
    )
