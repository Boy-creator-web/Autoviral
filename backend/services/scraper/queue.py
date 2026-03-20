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
        logger.info(
            "Queued scraper job job_id=%s queue=%s",
            job_id,
            settings.scraper_queue_name,
        )
    except RedisError:
        # Manual analyze should still run even if queue is temporarily unavailable.
        logger.exception("Failed to enqueue scraper job job_id=%s", job_id)

    return job_id
