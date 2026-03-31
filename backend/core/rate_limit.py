"""Redis-backed rate limiting and auth lock helpers."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from threading import Lock

from fastapi import HTTPException, Request, Response, status
from redis import Redis
from redis.exceptions import RedisError

from core.config import settings

_LOCAL_LOCK = Lock()
_LOCAL_RATE_STATE: dict[str, tuple[int, float]] = {}
_LOCAL_LOGIN_FAIL_STATE: dict[str, tuple[int, float]] = {}
_LOCAL_LOGIN_LOCK_STATE: dict[str, float] = {}


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
        # Fallback to local in-process limiter if Redis is down.
        now = time.time()
        with _LOCAL_LOCK:
            hits, expires_at = _LOCAL_RATE_STATE.get(key, (0, now + window))
            if now >= expires_at:
                hits, expires_at = 0, now + window
            hits += 1
            _LOCAL_RATE_STATE[key] = (hits, expires_at)
            ttl = max(0, int(expires_at - now))
            return hits, ttl


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
        now = time.time()
        key = _lock_key(scope, identifier)
        with _LOCAL_LOCK:
            expires_at = _LOCAL_LOGIN_LOCK_STATE.get(key)
            if expires_at is None:
                return 0
            ttl = int(expires_at - now)
            if ttl <= 0:
                _LOCAL_LOGIN_LOCK_STATE.pop(key, None)
                return 0
            return ttl


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
        now = time.time()
        fail_key = _fail_key(scope, identifier)
        lock_key = _lock_key(scope, identifier)
        with _LOCAL_LOCK:
            failures, fail_expires = _LOCAL_LOGIN_FAIL_STATE.get(
                fail_key, (0, now + settings.login_fail_window_seconds)
            )
            if now >= fail_expires:
                failures, fail_expires = 0, now + settings.login_fail_window_seconds
            failures += 1
            _LOCAL_LOGIN_FAIL_STATE[fail_key] = (failures, fail_expires)

            if failures >= settings.login_fail_max_attempts:
                lock_expires = now + settings.login_lock_seconds
                _LOCAL_LOGIN_LOCK_STATE[lock_key] = lock_expires
                _LOCAL_LOGIN_FAIL_STATE.pop(fail_key, None)
                return True, settings.login_lock_seconds
        return False, 0


def clear_login_failures(scope: str, identifier: str) -> None:
    try:
        client = _client()
        client.delete(_fail_key(scope, identifier))
        client.delete(_lock_key(scope, identifier))
    except RedisError:
        with _LOCAL_LOCK:
            _LOCAL_LOGIN_FAIL_STATE.pop(_fail_key(scope, identifier), None)
            _LOCAL_LOGIN_LOCK_STATE.pop(_lock_key(scope, identifier), None)
