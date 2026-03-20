"""Celery tasks for asynchronous scraper analysis."""

from __future__ import annotations

import logging
from typing import Any

from api.schemas import ScraperAnalyzeRequest
from core.celery_app import celery_app
from core.database import SessionLocal
from services.scraper.engine import run_manual_scraper_analysis
from services.scraper.queue import set_scraper_job_state

logger = logging.getLogger(__name__)


@celery_app.task(name="scraper.run_analysis", bind=True)
def run_scraper_analysis_task(self, *, payload: dict[str, Any]) -> dict[str, Any]:
    """Run scraper analysis in background worker and return persisted row IDs."""
    db = SessionLocal()
    task_id = str(self.request.id)
    try:
        set_scraper_job_state(task_id, state="processing")
        parsed_payload = ScraperAnalyzeRequest.model_validate(payload)
        rows = run_manual_scraper_analysis(db, payload=parsed_payload)
        row_ids = [row.id for row in rows]
        result_payload = {
            "topic": parsed_payload.topic,
            "saved_rows": len(row_ids),
            "scraper_data_ids": row_ids,
        }
        set_scraper_job_state(task_id, state="completed", result=result_payload)
        logger.info(
            "Completed scraper analysis task_id=%s topic=%s saved_rows=%d",
            task_id,
            parsed_payload.topic,
            len(row_ids),
        )
        return result_payload
    except Exception as err:
        set_scraper_job_state(task_id, state="failed", error=str(err))
        logger.exception("Scraper analysis task failed task_id=%s", task_id)
        raise
    finally:
        db.close()
