from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Response, status
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.celery_app import celery_app
from core.config import settings
from core.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/dependencies")
def dependency_health_check(
    response: Response,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Check connectivity to PostgreSQL, Redis, and Celery broker."""
    checks: dict[str, dict[str, Any]] = {
        "postgres": {"status": "unknown"},
        "redis": {"status": "unknown"},
        "celery_broker": {"status": "unknown"},
    }
    overall_status = "ok"

    try:
        db.execute(text("SELECT 1"))
        checks["postgres"]["status"] = "ok"
    except Exception as err:
        checks["postgres"] = {"status": "error", "detail": str(err)}
        overall_status = "degraded"
        logger.exception("PostgreSQL health check failed")

    try:
        redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
        redis_client.ping()
        checks["redis"] = {
            "status": "ok",
            "video_queue_length": redis_client.llen(settings.video_queue_name),
            "scraper_queue_length": redis_client.llen(settings.scraper_queue_name),
        }
    except RedisError as err:
        checks["redis"] = {"status": "error", "detail": str(err)}
        overall_status = "degraded"
        logger.exception("Redis health check failed")

    try:
        with celery_app.connection_for_read() as connection:
            connection.ensure_connection(max_retries=1)
        checks["celery_broker"] = {
            "status": "ok",
            "broker": settings.celery_broker_url,
        }
    except Exception as err:
        checks["celery_broker"] = {"status": "error", "detail": str(err)}
        overall_status = "degraded"
        logger.exception("Celery broker health check failed")

    if overall_status != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": overall_status,
        "checks": checks,
    }
