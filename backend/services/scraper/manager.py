"""Scraper async job orchestration and status lookup."""

from __future__ import annotations

import logging
from typing import Any

from celery.result import AsyncResult

from core.config import settings
from core.celery_app import celery_app
from services.scraper.queue import get_scraper_job_meta, register_scraper_job
from services.scraper.tasks import run_scraper_analysis_task

logger = logging.getLogger(__name__)


def queue_scraper_analysis_job(payload: dict[str, Any]) -> str:
    """Queue scraper analysis via Celery and return job id."""
    try:
        task = run_scraper_analysis_task.apply_async(
            kwargs={"payload": payload},
            queue=settings.scraper_queue_name,
        )
        register_scraper_job(job_id=task.id, payload=payload, mode="async")
        logger.info("Queued scraper Celery task job_id=%s", task.id)
        return task.id
    except Exception as err:
        logger.exception("Failed to queue scraper analysis job")
        raise RuntimeError("Failed to queue scraper analysis job") from err


def get_scraper_analysis_status(job_id: str) -> dict[str, Any]:
    """Read current status for scraper analysis job from Celery + Redis metadata."""
    try:
        result = AsyncResult(job_id, app=celery_app)
        meta = get_scraper_job_meta(job_id) or {}
        state = result.state
        if state == "PENDING" and meta.get("state") == "completed":
            state = "SUCCESS"
        elif state == "PENDING" and meta.get("state") == "failed":
            state = "FAILURE"

        resolved_result = result.result if result.successful() else meta.get("result")
        resolved_error = str(result.result) if result.failed() else meta.get("error")
        return {
            "job_id": job_id,
            "state": state,
            "result": resolved_result,
            "error": resolved_error,
            "meta": meta,
        }
    except Exception as err:
        logger.exception("Failed to fetch scraper status job_id=%s", job_id)
        raise RuntimeError("Failed to fetch scraper status") from err
