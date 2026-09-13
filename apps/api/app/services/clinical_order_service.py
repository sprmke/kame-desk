import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ActivityLog, ClinicalOrder
from app.schemas.clinical_order import ClinicalOrderCreate, ClinicalOrderUpdate
from app.services.patient_service import get_patient


async def list_orders(
    db: AsyncSession, clinic_id: uuid.UUID, patient_id: uuid.UUID
) -> list[ClinicalOrder]:
    await get_patient(db, clinic_id, patient_id)
    result = await db.execute(
        select(ClinicalOrder)
        .where(ClinicalOrder.clinic_id == clinic_id, ClinicalOrder.patient_id == patient_id)
        .order_by(ClinicalOrder.created_at.desc())
    )
    return list(result.scalars().all())


async def create_order(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    patient_id: uuid.UUID,
    data: ClinicalOrderCreate,
    actor_id: uuid.UUID,
) -> ClinicalOrder:
    await get_patient(db, clinic_id, patient_id)
    order = ClinicalOrder(
        clinic_id=clinic_id,
        patient_id=patient_id,
        appointment_id=data.appointment_id,
        order_type=data.order_type,
        name=data.name.strip(),
        status="ordered",
        created_by_user_id=actor_id,
    )
    db.add(order)
    await db.flush()
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor_id,
            actor_type="user",
            action="clinical_order.created",
            target_type="clinical_order",
            target_id=str(order.id),
            summary="Lab or imaging order placed",
        )
    )
    await db.commit()
    await db.refresh(order)
    return order


async def update_order(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    order_id: uuid.UUID,
    data: ClinicalOrderUpdate,
    actor_id: uuid.UUID,
) -> ClinicalOrder:
    result = await db.execute(
        select(ClinicalOrder).where(
            ClinicalOrder.id == order_id, ClinicalOrder.clinic_id == clinic_id
        )
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    payload = data.model_dump(exclude_unset=True)
    if "status" in payload and payload["status"]:
        order.status = payload["status"]
    if "result_summary" in payload:
        order.result_summary = payload["result_summary"]
    if "patient_file_id" in payload:
        order.patient_file_id = payload["patient_file_id"]
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor_id,
            actor_type="user",
            action="clinical_order.updated",
            target_type="clinical_order",
            target_id=str(order.id),
            summary="Lab or imaging order updated",
        )
    )
    await db.commit()
    await db.refresh(order)
    if "status" in payload and payload["status"]:
        from app.services.notification_service import notify_clinical_order_updated

        await notify_clinical_order_updated(
            db,
            clinic_id=clinic_id,
            order_id=order.id,
            patient_id=order.patient_id,
            doctor_user_id=order.created_by_user_id,
            status=order.status,
        )
    return order
