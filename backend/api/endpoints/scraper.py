"""Scraper engine API endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.schemas import (
    ScraperAnalyzeRequest,
    ScraperAnalyzeResponse,
    ScraperDataRead,
    ScraperJobStatusResponse,
)
from core.database import get_db
from services.scraper import (
    enqueue_scraper_job,
    get_scraper_analysis_status,
    list_scraper_insights,
    queue_scraper_analysis_job,
    run_manual_scraper_analysis,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analyze", response_model=ScraperAnalyzeResponse)
def analyze_scraper_manually(
    payload: ScraperAnalyzeRequest,
    run_async: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> ScraperAnalyzeResponse:
    """Trigger manual scraper analysis and persist all generated insights."""
    logger.info("Scraper analyze called topic=%s run_async=%s", payload.topic, run_async)
    try:
        if run_async:
            job_id = queue_scraper_analysis_job(payload.model_dump())
            return ScraperAnalyzeResponse(
                job_id=job_id,
                status="queued",
                results=[],
            )

        job_id = enqueue_scraper_job(payload.model_dump())
        results = run_manual_scraper_analysis(db, payload=payload)
        return ScraperAnalyzeResponse(
            job_id=job_id,
            status="completed",
            results=[ScraperDataRead.model_validate(row) for row in results],
        )
    except RuntimeError as err:
        logger.exception("analyze_scraper_manually failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(err),
        ) from err


@router.get("/insights", response_model=list[ScraperDataRead])
def get_scraper_insights(
    limit: int = Query(default=50, ge=1, le=500),
    topic: str | None = Query(default=None, min_length=1, max_length=255),
    db: Session = Depends(get_db),
) -> list[ScraperDataRead]:
    """Return persisted scraper insights from ScraperData table."""
    rows = list_scraper_insights(db, limit=limit, topic=topic)
    return [ScraperDataRead.model_validate(row) for row in rows]


@router.get("/status/{job_id}", response_model=ScraperJobStatusResponse)
def get_scraper_job_status(job_id: str) -> ScraperJobStatusResponse:
    """Get scraper job execution status for asynchronous analyze requests."""
    try:
        payload = get_scraper_analysis_status(job_id)
        return ScraperJobStatusResponse.model_validate(payload)
    except RuntimeError as err:
        logger.exception("get_scraper_job_status failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(err),
        ) from err
