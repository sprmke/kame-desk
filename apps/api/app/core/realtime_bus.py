"""Redis pub/sub bridge so API workers and ARQ share clinic WebSocket broadcasts."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any

from redis.asyncio import Redis

from app.core.config import settings
from app.core.ws_manager import clinic_ws_manager

logger = logging.getLogger(__name__)

REALTIME_CHANNEL_PREFIX = "clinic:"
REALTIME_CHANNEL_SUFFIX = ":realtime"

_subscriber_task: asyncio.Task[None] | None = None


def clinic_channel(clinic_id: uuid.UUID) -> str:
    return f"{REALTIME_CHANNEL_PREFIX}{clinic_id}{REALTIME_CHANNEL_SUFFIX}"


def _clinic_id_from_channel(channel: str) -> uuid.UUID | None:
    if not channel.startswith(REALTIME_CHANNEL_PREFIX) or not channel.endswith(
        REALTIME_CHANNEL_SUFFIX
    ):
        return None
    raw = channel[len(REALTIME_CHANNEL_PREFIX) : -len(REALTIME_CHANNEL_SUFFIX)]
    try:
        return uuid.UUID(raw)
    except ValueError:
        return None


async def publish_clinic_event(clinic_id: uuid.UUID, event: str, data: dict[str, Any]) -> None:
    """Publish to Redis; local WS connections also receive via subscriber on this process."""
    payload = json.dumps({"event": event, "data": data})
    redis: Redis | None = None
    try:
        redis = Redis.from_url(settings.redis_url, decode_responses=True)
        await redis.publish(clinic_channel(clinic_id), payload)
    except Exception:
        logger.exception("Redis publish failed clinic_id=%s event=%s", clinic_id, event)
    finally:
        if redis is not None:
            await redis.aclose()


async def _subscriber_loop() -> None:
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    pubsub = redis.pubsub()
    pattern = f"{REALTIME_CHANNEL_PREFIX}*{REALTIME_CHANNEL_SUFFIX}"
    await pubsub.psubscribe(pattern)
    try:
        async for message in pubsub.listen():
            if message["type"] != "pmessage":
                continue
            channel = message.get("channel") or ""
            clinic_id = _clinic_id_from_channel(channel)
            if clinic_id is None:
                continue
            try:
                parsed = json.loads(message["data"])
                event = parsed.get("event", "")
                data = parsed.get("data") or {}
                await clinic_ws_manager.broadcast(clinic_id, event, data)
            except Exception:
                logger.exception("Realtime subscriber failed channel=%s", channel)
    except asyncio.CancelledError:
        raise
    finally:
        await pubsub.unsubscribe(pattern)
        await pubsub.aclose()
        await redis.aclose()


async def start_realtime_subscriber() -> None:
    global _subscriber_task
    if _subscriber_task is not None:
        return
    _subscriber_task = asyncio.create_task(_subscriber_loop(), name="realtime-subscriber")


async def stop_realtime_subscriber() -> None:
    global _subscriber_task
    if _subscriber_task is None:
        return
    _subscriber_task.cancel()
    try:
        await _subscriber_task
    except asyncio.CancelledError:
        pass
    _subscriber_task = None
