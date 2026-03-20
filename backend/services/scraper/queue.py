"""Redis queue integration for scraper jobs."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from redis import Redis
from redis.exceptions import RedisError

from core.config import settings

logger = logging.getLogger(__name__)


def enqueue_scraper_job(payload: dict[str, Any]) -> str:
    """Push a scraper job payload to Redis and return generated job id."""
    job_id = str(uuid4())
    register_scraper_job(job_id=job_id, payload=payload)
    return job_id


def register_scraper_job(*, job_id: str, payload: dict[str, Any]) -> None:
    """Register scraper job metadata into Redis for observability."""
    message = {
        "job_id": job_id,
        "queued_at": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
    }

    try:
        redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
        redis_client.rpush(
            settings.scraper_queue_name,
            json.dumps(message, ensure_ascii=True),
        )
        redis_client.set(
            f"scraper:job:{job_id}",
            json.dumps(
                {
                    "job_id": job_id,
                    "topic": payload.get("topic"),
                    "queued_at": message["queued_at"],
                },
                ensure_ascii=True,
            ),
            ex=86400,
        )
        logger.info(
            "Queued scraper job job_id=%s queue=%s",
            job_id,
            settings.scraper_queue_name,
        )
    except RedisError:
        # Analyze should still run even if queue is temporarily unavailable.
        logger.exception("Failed to enqueue scraper job job_id=%s", job_id)


def get_scraper_job_meta(job_id: str) -> dict[str, Any] | None:
    """Fetch scraper job metadata from Redis cache."""
    try:
        redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
        raw = redis_client.get(f"scraper:job:{job_id}")
        if raw is None:
            return None
        return json.loads(raw)
    except (RedisError, json.JSONDecodeError):
        logger.exception("Failed to fetch scraper job metadata job_id=%s", job_id)
        return None
