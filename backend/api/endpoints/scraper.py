"""Scraper engine API endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.schemas import ScraperAnalyzeRequest, ScraperAnalyzeResponse, ScraperDataRead
from core.database import get_db
from services.scraper import (
    enqueue_scraper_job,
    list_scraper_insights,
    run_manual_scraper_analysis,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analyze", response_model=ScraperAnalyzeResponse)
def analyze_scraper_manually(
    payload: ScraperAnalyzeRequest,
    db: Session = Depends(get_db),
) -> ScraperAnalyzeResponse:
    """Trigger manual scraper analysis and persist all generated insights."""
    logger.info("Manual scraper analyze called topic=%s", payload.topic)
    job_id = enqueue_scraper_job(payload.model_dump())
    results = run_manual_scraper_analysis(db, payload=payload)
    return ScraperAnalyzeResponse(
        job_id=job_id,
        results=[ScraperDataRead.model_validate(row) for row in results],
    )


@router.get("/insights", response_model=list[ScraperDataRead])
def get_scraper_insights(
    limit: int = Query(default=50, ge=1, le=500),
    topic: str | None = Query(default=None, min_length=1, max_length=255),
    db: Session = Depends(get_db),
) -> list[ScraperDataRead]:
    """Return persisted scraper insights from ScraperData table."""
    rows = list_scraper_insights(db, limit=limit, topic=topic)
    return [ScraperDataRead.model_validate(row) for row in rows]
