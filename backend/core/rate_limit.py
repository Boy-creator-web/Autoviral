"""Redis-backed rate limiting and auth lock helpers."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from fastapi import HTTPException, Request, Response, status
from redis import Redis
from redis.exceptions import RedisError

from core.config import settings


@dataclass
class RateLimitResult:
    """Snapshot of a limiter decision for response headers."""

    scope: str
    limit: int
    remaining: int
    reset_seconds: int

    def as_headers(self) -> dict[str, str]:
        return {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(self.remaining),
            "X-RateLimit-Reset": str(self.reset_seconds),
        }


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


def _build_result(scope: str, *, hits: int, ttl: int, limit: int) -> RateLimitResult:
    return RateLimitResult(
        scope=scope,
        limit=limit,
        remaining=max(0, limit - hits),
        reset_seconds=max(0, ttl),
    )


def enforce_ip_rate_limit(request: Request) -> RateLimitResult:
    ip = request.client.host if request.client else "unknown"
    limit = settings.rate_limit_requests
    hits, ttl = _hit("ip", ip, limit=limit, window=settings.rate_limit_window_seconds)
    result = _build_result("ip", hits=hits, ttl=ttl, limit=limit)
    if hits > limit:
        headers = result.as_headers()
        headers["Retry-After"] = str(result.reset_seconds)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Retry in {result.reset_seconds}s",
            headers=headers,
        )
    return result


def enforce_user_rate_limit(user_id: int, *, factor: int = 2) -> RateLimitResult:
    limit = settings.rate_limit_requests * max(1, factor)
    hits, ttl = _hit("user", str(user_id), limit=limit, window=settings.rate_limit_window_seconds)
    result = _build_result("user", hits=hits, ttl=ttl, limit=limit)
    if hits > limit:
        headers = result.as_headers()
        headers["Retry-After"] = str(result.reset_seconds)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"User rate limit exceeded. Retry in {result.reset_seconds}s",
            headers=headers,
        )
    return result


def apply_rate_limit_headers(response: Response, *results: RateLimitResult) -> None:
    """Attach canonical X-RateLimit-* headers from strictest result."""
    if not results:
        return
    strictest = min(results, key=lambda item: item.remaining)
    for header, value in strictest.as_headers().items():
        response.headers[header] = value


def _lock_key(scope: str, identifier: str) -> str:
    return f"auth:lock:{scope}:{_safe_segment(identifier)}"


def _fail_key(scope: str, identifier: str) -> str:
    return f"auth:fail:{scope}:{_safe_segment(identifier)}"


def check_login_lock(scope: str, identifier: str) -> int:
    """Return lock TTL seconds if locked, else 0."""
    try:
        client = _client()
        ttl = int(client.ttl(_lock_key(scope, identifier)))
        return ttl if ttl > 0 else 0
    except RedisError:
        return 0


def register_login_failure(scope: str, identifier: str) -> tuple[bool, int]:
    """
    Register a failed login attempt.

    Returns: (locked_now, lock_ttl_seconds)
    """
    try:
        client = _client()
        counter_key = _fail_key(scope, identifier)
        failures = int(client.incr(counter_key))
        if failures == 1:
            client.expire(counter_key, settings.login_fail_window_seconds)

        if failures >= settings.login_fail_max_attempts:
            lock_key = _lock_key(scope, identifier)
            client.set(lock_key, "1", ex=settings.login_lock_seconds)
            client.delete(counter_key)
            return True, settings.login_lock_seconds
        return False, 0
    except RedisError:
        return False, 0


def clear_login_failures(scope: str, identifier: str) -> None:
    try:
        client = _client()
        client.delete(_fail_key(scope, identifier))
        client.delete(_lock_key(scope, identifier))
    except RedisError:
        return
