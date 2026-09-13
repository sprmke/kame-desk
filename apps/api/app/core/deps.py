import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_active_clinic_membership, require_clinic_role
from app.models import Clinic, ClinicMembership
from app.services.clinic_service import get_clinic


async def clinic_from_path(
    clinic_id: Annotated[uuid.UUID, Path()],
    membership: Annotated[ClinicMembership, Depends(get_active_clinic_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Clinic:
    if membership.clinic_id != clinic_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Clinic scope mismatch")
    return await get_clinic(db, clinic_id)


OwnerAdmin = Annotated[ClinicMembership, Depends(require_clinic_role("owner", "admin"))]
OwnerOnly = Annotated[ClinicMembership, Depends(require_clinic_role("owner"))]
ClinicStaff = Annotated[
    ClinicMembership,
    Depends(require_clinic_role("owner", "admin", "doctor", "reception")),
]
AnyMember = Annotated[ClinicMembership, Depends(get_active_clinic_membership)]
