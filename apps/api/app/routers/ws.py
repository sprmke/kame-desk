import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.db import AsyncSessionLocal
from app.core.security import get_user_from_access_token, verify_clinic_membership
from app.core.ws_manager import clinic_ws_manager

router = APIRouter()


@router.websocket("/ws/clinic/{clinic_id}")
async def clinic_websocket(websocket: WebSocket, clinic_id: uuid.UUID) -> None:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401)
        return

    async with AsyncSessionLocal() as db:
        try:
            user = await get_user_from_access_token(token, db)
            await verify_clinic_membership(user, clinic_id, db)
        except Exception:
            await websocket.close(code=4401)
            return

    await clinic_ws_manager.connect(clinic_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        clinic_ws_manager.disconnect(clinic_id, websocket)
