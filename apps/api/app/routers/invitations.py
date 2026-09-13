from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.clinic import InvitationAccept
from app.services import clinic_service

router = APIRouter(prefix="/invitations", tags=["invitations"])


@router.post("/{token}/accept", status_code=204)
async def accept_invitation(
    token: str,
    data: InvitationAccept,
    db: AsyncSession = Depends(get_db),
) -> None:
    await clinic_service.accept_invitation(db, token, data)
