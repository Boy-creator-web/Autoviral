"""Scraper engine orchestration and insight retrieval."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.schemas import ScraperAnalyzeRequest
from models.scraper_data import ScraperData
from services.scraper.competitor_hole import run_deep_competitor_hole
from services.scraper.competitor_watch import run_competitor_death_watch
from services.scraper.emotion_analyzer import run_emotional_intelligence
from services.scraper.intent_detector import run_micro_conversion_signal
from services.scraper.intent_scorer import run_purchase_intent_scoring
from services.scraper.trend_forecast import run_trend_forecast

logger = logging.getLogger(__name__)


def run_manual_scraper_analysis(
    db: Session,
    *,
    payload: ScraperAnalyzeRequest,
) -> list[ScraperData]:
    """Execute all scraper intelligence features and persist each result."""
    logger.info("Running scraper engine for topic=%s", payload.topic)
    results = [
        run_competitor_death_watch(
            db,
            topic=payload.topic,
            competitor_signals=payload.competitor_signals,
        ),
        run_trend_forecast(
            db,
            topic=payload.topic,
            trend_points=payload.trend_points,
        ),
        run_micro_conversion_signal(
            db,
            topic=payload.topic,
            user_actions=payload.user_actions,
        ),
        run_emotional_intelligence(
            db,
            topic=payload.topic,
            comments=payload.comments,
        ),
        run_deep_competitor_hole(
            db,
            topic=payload.topic,
            competitor_contents=payload.competitor_contents,
            pain_points=payload.pain_points,
        ),
        run_purchase_intent_scoring(
            db,
            topic=payload.topic,
            lead_signals=payload.lead_signals,
        ),
    ]
    logger.info("Scraper engine completed topic=%s saved_rows=%d", payload.topic, len(results))
    return results


def list_scraper_insights(
    db: Session,
    *,
    limit: int = 50,
    topic: str | None = None,
) -> list[ScraperData]:
    """Read latest scraper insights with optional topic filter."""
    statement = select(ScraperData).order_by(ScraperData.id.desc()).limit(limit)
    if topic:
        statement = statement.where(ScraperData.topic == topic)
    return list(db.scalars(statement).all())
