from fastapi import APIRouter

from app.services.platform_service import PLANS

router = APIRouter(prefix="/plans", tags=["plans"])


@router.get("")
async def list_public_plans() -> list[dict]:
    return list(PLANS)
