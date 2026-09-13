import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ClinicMembership, Payer
from app.schemas.payer_workflow import PayerCreate, PayerUpdate
from app.services.billing_access import assert_billing_read, assert_billing_write


async def list_payers(
    db: AsyncSession, clinic_id: uuid.UUID, membership: ClinicMembership
) -> list[Payer]:
    assert_billing_read(membership)
    result = await db.execute(
        select(Payer).where(Payer.clinic_id == clinic_id).order_by(Payer.name)
    )
    return list(result.scalars().all())


async def create_payer(
    db: AsyncSession, clinic_id: uuid.UUID, data: PayerCreate, membership: ClinicMembership
) -> Payer:
    assert_billing_write(membership)
    payer = Payer(clinic_id=clinic_id, name=data.name.strip(), payer_type=data.payer_type)
    db.add(payer)
    await db.commit()
    await db.refresh(payer)
    return payer


async def update_payer(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    payer_id: uuid.UUID,
    data: PayerUpdate,
    membership: ClinicMembership,
) -> Payer:
    assert_billing_write(membership)
    result = await db.execute(
        select(Payer).where(Payer.id == payer_id, Payer.clinic_id == clinic_id)
    )
    payer = result.scalar_one_or_none()
    if payer is None:
        raise HTTPException(status_code=404, detail="Payer not found")
    payload = data.model_dump(exclude_unset=True)
    for key, value in payload.items():
        setattr(payer, key, value)
    await db.commit()
    await db.refresh(payer)
    return payer
