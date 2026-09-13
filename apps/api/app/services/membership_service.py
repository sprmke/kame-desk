import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    ActivityLog,
    Invoice,
    InvoiceLineItem,
    MembershipPlan,
    PatientMembership,
)
from app.schemas.membership import MembershipPlanCreate, MembershipPlanUpdate
from app.services.patient_service import get_patient

_INTERVAL_MONTHS = {"monthly": 1, "quarterly": 3, "annual": 12}


def _period_end(start: date, billing_interval: str) -> date:
    return start + relativedelta(months=_INTERVAL_MONTHS[billing_interval])


async def list_plans(
    db: AsyncSession, clinic_id: uuid.UUID, *, active_only: bool = False
) -> list[MembershipPlan]:
    query = select(MembershipPlan).where(MembershipPlan.clinic_id == clinic_id)
    if active_only:
        query = query.where(MembershipPlan.is_active.is_(True))
    result = await db.execute(query.order_by(MembershipPlan.name))
    return list(result.scalars().all())


async def create_plan(
    db: AsyncSession, clinic_id: uuid.UUID, data: MembershipPlanCreate, actor_id: uuid.UUID
) -> MembershipPlan:
    plan = MembershipPlan(
        clinic_id=clinic_id,
        name=data.name,
        price=data.price,
        billing_interval=data.billing_interval,
        included_services=[s.model_dump() for s in data.included_services],
    )
    db.add(plan)
    await db.flush()
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor_id,
            actor_type="user",
            action="membership_plan.created",
            target_type="membership_plan",
            target_id=str(plan.id),
            summary=f"Membership plan '{plan.name}' created",
        )
    )
    await db.commit()
    await db.refresh(plan)
    return plan


async def get_plan(db: AsyncSession, clinic_id: uuid.UUID, plan_id: uuid.UUID) -> MembershipPlan:
    result = await db.execute(
        select(MembershipPlan).where(
            MembershipPlan.id == plan_id, MembershipPlan.clinic_id == clinic_id
        )
    )
    plan = result.scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=404, detail="Membership plan not found")
    return plan


async def update_plan(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    plan_id: uuid.UUID,
    data: MembershipPlanUpdate,
    actor_id: uuid.UUID,
) -> MembershipPlan:
    plan = await get_plan(db, clinic_id, plan_id)
    payload = data.model_dump(exclude_unset=True)
    if "included_services" in payload and payload["included_services"] is not None:
        payload["included_services"] = [
            s if isinstance(s, dict) else s.model_dump() for s in data.included_services
        ]
    for field, value in payload.items():
        setattr(plan, field, value)
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor_id,
            actor_type="user",
            action="membership_plan.updated",
            target_type="membership_plan",
            target_id=str(plan.id),
            summary=f"Membership plan '{plan.name}' updated",
        )
    )
    await db.commit()
    await db.refresh(plan)
    return plan


async def enroll_patient(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    patient_id: uuid.UUID,
    plan_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> PatientMembership:
    await get_patient(db, clinic_id, patient_id)
    plan = await get_plan(db, clinic_id, plan_id)
    if not plan.is_active:
        raise HTTPException(status_code=400, detail="Plan is not active")

    existing = await get_active_membership(db, clinic_id, patient_id)
    if existing is not None:
        raise HTTPException(status_code=409, detail="Patient already has an active membership")

    today = datetime.now(UTC).date()
    membership = PatientMembership(
        clinic_id=clinic_id,
        patient_id=patient_id,
        plan_id=plan.id,
        status="active",
        started_at=today,
        current_period_end=_period_end(today, plan.billing_interval),
        usage_this_period={},
    )
    db.add(membership)
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor_id,
            actor_type="user",
            action="membership.enrolled",
            target_type="patient_membership",
            target_id=str(membership.id) if membership.id else None,
            summary=f"Enrolled in membership plan '{plan.name}'",
        )
    )
    await db.commit()
    await db.refresh(membership)
    return membership


async def cancel_membership(
    db: AsyncSession, clinic_id: uuid.UUID, membership_id: uuid.UUID, actor_id: uuid.UUID
) -> PatientMembership:
    result = await db.execute(
        select(PatientMembership).where(
            PatientMembership.id == membership_id, PatientMembership.clinic_id == clinic_id
        )
    )
    membership = result.scalar_one_or_none()
    if membership is None:
        raise HTTPException(status_code=404, detail="Membership not found")
    membership.status = "cancelled"
    membership.cancelled_at = datetime.now(UTC)
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor_id,
            actor_type="user",
            action="membership.cancelled",
            target_type="patient_membership",
            target_id=str(membership.id),
            summary="Membership cancelled",
        )
    )
    await db.commit()
    await db.refresh(membership)
    return membership


async def get_active_membership(
    db: AsyncSession, clinic_id: uuid.UUID, patient_id: uuid.UUID
) -> PatientMembership | None:
    result = await db.execute(
        select(PatientMembership).where(
            PatientMembership.clinic_id == clinic_id,
            PatientMembership.patient_id == patient_id,
            PatientMembership.status == "active",
        )
    )
    membership = result.scalar_one_or_none()
    if membership is None:
        return None

    today = datetime.now(UTC).date()
    if membership.current_period_end < today:
        plan = await db.get(MembershipPlan, membership.plan_id)
        if plan is None:
            membership.status = "expired"
            await db.commit()
            return None
        # Roll forward to the current period, resetting usage counters.
        while membership.current_period_end < today:
            membership.started_at = membership.current_period_end
            membership.current_period_end = _period_end(
                membership.current_period_end, plan.billing_interval
            )
        membership.usage_this_period = {}
        await db.commit()
        await db.refresh(membership)
    return membership


async def maybe_apply_membership_waiver(
    db: AsyncSession,
    invoice: Invoice,
    line_item: InvoiceLineItem,
    *,
    clinic_id: uuid.UUID,
) -> None:
    """If the invoice's patient has an active membership covering this line
    item's category, add a matching negative discount line and record usage.
    Never raises — a waiver failure must not block invoice creation."""
    try:
        membership = await get_active_membership(db, clinic_id, invoice.patient_id)
        if membership is None:
            return
        plan = await db.get(MembershipPlan, membership.plan_id)
        if plan is None:
            return
        allowance = next(
            (
                s.get("count_per_period", 0)
                for s in plan.included_services or []
                if s.get("category") == line_item.category
            ),
            0,
        )
        if allowance <= 0:
            return
        used = int((membership.usage_this_period or {}).get(line_item.category, 0))
        if used >= allowance:
            return

        sort_order = max((i.sort_order for i in invoice.line_items), default=-1) + 1
        db.add(
            InvoiceLineItem(
                invoice_id=invoice.id,
                description=f"Membership benefit ({plan.name})",
                category=line_item.category,
                quantity=Decimal("1"),
                unit_price=-line_item.amount,
                amount=-line_item.amount,
                sort_order=sort_order,
            )
        )
        usage = dict(membership.usage_this_period or {})
        usage[line_item.category] = used + 1
        membership.usage_this_period = usage
        await db.flush()
    except Exception:
        import logging

        logging.getLogger(__name__).exception(
            "Membership waiver failed invoice=%s line_item=%s", invoice.id, line_item.id
        )
