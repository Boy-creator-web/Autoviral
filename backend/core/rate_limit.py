"""Simple Redis-backed rate limiter utilities."""

from __future__ import annotations

import hashlib
from typing import Any

from fastapi import HTTPException, Request, status
from redis import Redis
from redis.exceptions import RedisError

from core.config import settings


def _client() -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)


def _safe_segment(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return digest[:24]


def _key(scope: str, identifier: str) -> str:
    return f"rate:{scope}:{_safe_segment(identifier)}"


def _hit(scope: str, identifier: str, *, limit: int, window: int) -> tuple[int, int]:
    key = _key(scope, identifier)
    try:
        client = _client()
        hits = client.incr(key)
        if hits == 1:
            client.expire(key, window)
        ttl = client.ttl(key)
        return int(hits), int(ttl if ttl >= 0 else window)
    except RedisError:
        # Fail-open to prevent accidental outage if Redis is down.
        return 1, window


def enforce_ip_rate_limit(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    hits, ttl = _hit(
        "ip",
        ip,
        limit=settings.rate_limit_requests,
        window=settings.rate_limit_window_seconds,
    )
    if hits > settings.rate_limit_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Retry in {ttl}s",
        )


def enforce_user_rate_limit(user_id: int, *, factor: int = 2) -> None:
    limit = settings.rate_limit_requests * max(1, factor)
    hits, ttl = _hit(
        "user",
        str(user_id),
        limit=limit,
        window=settings.rate_limit_window_seconds,
    )
    if hits > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"User rate limit exceeded. Retry in {ttl}s",
        )
