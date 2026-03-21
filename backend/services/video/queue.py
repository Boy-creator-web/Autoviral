"""Redis-backed queue metadata for video rendering jobs."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from redis import Redis
from redis.exceptions import RedisError

from core.config import settings

logger = logging.getLogger(__name__)


def _client() -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)


def register_render_job(job_id: str, payload: dict[str, Any]) -> None:
    """Store rendering job metadata in Redis list for observability."""
    message = {
        "job_id": job_id,
        "queued_at": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
    }
    try:
        _client().rpush(settings.video_queue_name, json.dumps(message, ensure_ascii=True))
        logger.info("Registered render job id=%s queue=%s", job_id, settings.video_queue_name)
    except RedisError:
        logger.exception("Failed to register render job id=%s", job_id)


def set_job_video_mapping(job_id: str, video_id: int) -> None:
    """Cache task-to-video mapping in Redis for quick status lookup."""
    try:
        _client().set(f"video:job:{job_id}", str(video_id), ex=86400)
    except RedisError:
        logger.exception("Failed to map job id=%s to video=%s", job_id, video_id)


def set_job_runpod_mapping(job_id: str, runpod_job_id: str) -> None:
    """Cache Celery job to RunPod job id mapping for status endpoint."""
    try:
        _client().set(f"video:runpod:{job_id}", runpod_job_id, ex=86400)
    except RedisError:
        logger.exception("Failed to map job id=%s to runpod_job_id=%s", job_id, runpod_job_id)


def get_job_runpod_mapping(job_id: str) -> str | None:
    """Return RunPod job id mapped to Celery job, if present."""
    try:
        value = _client().get(f"video:runpod:{job_id}")
        return str(value) if value is not None else None
    except RedisError:
        logger.exception("Failed to fetch runpod mapping job_id=%s", job_id)
        return None


def get_job_video_mapping(job_id: str) -> int | None:
    """Return video id mapped to Celery job, if present."""
    try:
        value = _client().get(f"video:job:{job_id}")
        return int(value) if value is not None else None
    except (RedisError, ValueError):
        logger.exception("Failed to fetch job mapping job_id=%s", job_id)
        return None
