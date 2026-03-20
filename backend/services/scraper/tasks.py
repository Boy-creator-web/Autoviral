"""Celery tasks for asynchronous scraper analysis."""

from __future__ import annotations

import logging
from typing import Any

from api.schemas import ScraperAnalyzeRequest
from core.celery_app import celery_app
from core.database import SessionLocal
from services.scraper.engine import run_manual_scraper_analysis

logger = logging.getLogger(__name__)


@celery_app.task(name="scraper.run_analysis", bind=True)
def run_scraper_analysis_task(self, *, payload: dict[str, Any]) -> dict[str, Any]:
    """Run scraper analysis in background worker and return persisted row IDs."""
    db = SessionLocal()
    try:
        parsed_payload = ScraperAnalyzeRequest.model_validate(payload)
        rows = run_manual_scraper_analysis(db, payload=parsed_payload)
        row_ids = [row.id for row in rows]
        logger.info(
            "Completed scraper analysis task_id=%s topic=%s saved_rows=%d",
            self.request.id,
            parsed_payload.topic,
            len(row_ids),
        )
        return {
            "topic": parsed_payload.topic,
            "saved_rows": len(row_ids),
            "scraper_data_ids": row_ids,
        }
    except Exception as err:
        logger.exception("Scraper analysis task failed task_id=%s", self.request.id)
        raise
    finally:
        db.close()
