import uuid
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = {}

    async def connect(self, clinic_id: uuid.UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        key = str(clinic_id)
        self._connections.setdefault(key, set()).add(websocket)

    def disconnect(self, clinic_id: uuid.UUID, websocket: WebSocket) -> None:
        key = str(clinic_id)
        bucket = self._connections.get(key)
        if not bucket:
            return
        bucket.discard(websocket)
        if not bucket:
            self._connections.pop(key, None)

    async def broadcast(self, clinic_id: uuid.UUID, event: str, data: dict[str, Any]) -> None:
        key = str(clinic_id)
        payload = {"event": event, "data": data}
        dead: list[WebSocket] = []
        for ws in list(self._connections.get(key, set())):
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(clinic_id, ws)


clinic_ws_manager = ConnectionManager()
