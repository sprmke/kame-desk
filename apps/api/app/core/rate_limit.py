import time
from collections import defaultdict

from fastapi import HTTPException, Request

_WINDOW_SECONDS = 60
_MAX_REQUESTS = 30

_buckets: dict[str, list[float]] = defaultdict(list)


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def enforce_public_rate_limit(request: Request, slug: str) -> None:
    key = f"{client_ip(request)}:{slug}"
    now = time.time()
    bucket = [t for t in _buckets[key] if now - t < _WINDOW_SECONDS]
    if len(bucket) >= _MAX_REQUESTS:
        raise HTTPException(status_code=429, detail="Too many requests")
    bucket.append(now)
    _buckets[key] = bucket
