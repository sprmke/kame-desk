import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.models import User
from app.schemas.organization import (
    CreateClinicUnderOrgRequest,
    CreateClinicUnderOrgResponse,
    EnrolledClinicRead,
    OrganizationCreate,
    OrganizationDetailRead,
    OrganizationRead,
    OrgSeatSummaryRead,
)
from app.services import organization_service as org_service
from app.services.seat_service import org_seat_summary

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("", response_model=list[OrganizationRead])
async def list_organizations(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[OrganizationRead]:
    return await org_service.list_user_organizations(db, user)


@router.post("", response_model=OrganizationRead, status_code=201)
async def create_organization(
    data: OrganizationCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OrganizationRead:
    org = await org_service.create_organization_with_subscription(db, user, data.name)
    await db.commit()
    await db.refresh(org)
    return OrganizationRead(
        id=org.id,
        name=org.name,
        slug=org.slug,
        status=org.status,
        is_owner=True,
    )


@router.get("/{org_id}", response_model=OrganizationDetailRead)
async def get_organization(
    org_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OrganizationDetailRead:
    return await org_service.get_organization_detail(db, org_id, user)


@router.post("/{org_id}/clinics", response_model=CreateClinicUnderOrgResponse, status_code=201)
async def create_clinic_under_org(
    org_id: uuid.UUID,
    data: CreateClinicUnderOrgRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CreateClinicUnderOrgResponse:
    org = await org_service.assert_org_owner(db, user, org_id)
    clinic, enrollment = await org_service.create_clinic_under_org(
        db, org, user, data, enrollment_status="pending_enrollment"
    )
    await db.commit()
    await db.refresh(clinic)
    await db.refresh(enrollment)
    return CreateClinicUnderOrgResponse(
        clinic_id=clinic.id,
        clinic_name=clinic.name,
        clinic_slug=clinic.slug,
        enrollment_status=enrollment.status,
        organization_id=org.id,
    )


@router.get("/{org_id}/seat-summary", response_model=OrgSeatSummaryRead)
async def get_org_seat_summary(
    org_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OrgSeatSummaryRead:
    await org_service.assert_org_owner(db, user, org_id)
    return await org_seat_summary(db, org_id)


@router.get("/{org_id}/enrollments", response_model=list[EnrolledClinicRead])
async def list_org_enrollments(
    org_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[EnrolledClinicRead]:
    if not await org_service.user_can_access_org(db, user, org_id):
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="No access to organization")
    return await org_service.list_enrollments(db, org_id)
