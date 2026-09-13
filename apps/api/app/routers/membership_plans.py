import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import ClinicStaff, OwnerAdmin
from app.core.security import get_active_clinic_membership, get_current_user
from app.models import ClinicMembership, User
from app.schemas.membership import (
    MembershipPlanCreate,
    MembershipPlanRead,
    MembershipPlanUpdate,
    PatientMembershipEnroll,
    PatientMembershipRead,
)
from app.services import membership_service
from app.services.billing_access import assert_billing_write
from app.services.clinic_service import get_clinic

router = APIRouter(tags=["membership-plans"])


async def _clinic_id(
    membership: Annotated[ClinicMembership, Depends(get_active_clinic_membership)],
) -> uuid.UUID:
    return membership.clinic_id


@router.get("/clinics/{clinic_id}/membership-plans", response_model=list[MembershipPlanRead])
async def get_membership_plans(
    clinic_id: uuid.UUID,
    membership: ClinicStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[MembershipPlanRead]:
    await get_clinic(db, clinic_id)
    plans = await membership_service.list_plans(db, clinic_id)
    return [MembershipPlanRead.model_validate(p) for p in plans]


@router.post("/clinics/{clinic_id}/membership-plans", response_model=MembershipPlanRead)
async def post_membership_plan(
    clinic_id: uuid.UUID,
    data: MembershipPlanCreate,
    membership: OwnerAdmin,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MembershipPlanRead:
    await get_clinic(db, clinic_id)
    plan = await membership_service.create_plan(db, clinic_id, data, user.id)
    return MembershipPlanRead.model_validate(plan)


@router.patch("/clinics/{clinic_id}/membership-plans/{plan_id}", response_model=MembershipPlanRead)
async def patch_membership_plan(
    clinic_id: uuid.UUID,
    plan_id: uuid.UUID,
    data: MembershipPlanUpdate,
    membership: OwnerAdmin,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MembershipPlanRead:
    plan = await membership_service.update_plan(db, clinic_id, plan_id, data, user.id)
    return MembershipPlanRead.model_validate(plan)


def _to_read(m, plan_name: str | None) -> PatientMembershipRead:
    row = PatientMembershipRead.model_validate(m)
    row.plan_name = plan_name
    return row


@router.get("/patients/{patient_id}/membership", response_model=PatientMembershipRead | None)
async def get_patient_membership(
    patient_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PatientMembershipRead | None:
    active = await membership_service.get_active_membership(db, clinic_id, patient_id)
    if active is None:
        return None
    plan = await membership_service.get_plan(db, clinic_id, active.plan_id)
    return _to_read(active, plan.name)


@router.post("/patients/{patient_id}/membership", response_model=PatientMembershipRead)
async def post_patient_membership(
    patient_id: uuid.UUID,
    data: PatientMembershipEnroll,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PatientMembershipRead:
    assert_billing_write(membership)
    enrolled = await membership_service.enroll_patient(
        db, clinic_id, patient_id, data.plan_id, user.id
    )
    plan = await membership_service.get_plan(db, clinic_id, enrolled.plan_id)
    return _to_read(enrolled, plan.name)


@router.post(
    "/patients/{patient_id}/membership/{membership_id}/cancel",
    response_model=PatientMembershipRead,
)
async def post_cancel_membership(
    patient_id: uuid.UUID,
    membership_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PatientMembershipRead:
    assert_billing_write(membership)
    cancelled = await membership_service.cancel_membership(db, clinic_id, membership_id, user.id)
    plan = await membership_service.get_plan(db, clinic_id, cancelled.plan_id)
    return _to_read(cancelled, plan.name)
