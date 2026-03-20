"""Emotional Intelligence feature implementation."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from models.scraper_data import ScraperData
from services.scraper.common import clamp_score, persist_scraper_result

logger = logging.getLogger(__name__)

POSITIVE_TERMS = {
    "love",
    "great",
    "helpful",
    "amazing",
    "easy",
    "fast",
    "recommended",
    "satisfied",
}
NEGATIVE_TERMS = {
    "hate",
    "bad",
    "slow",
    "broken",
    "difficult",
    "expensive",
    "confusing",
    "bug",
}


def run_emotional_intelligence(
    db: Session,
    *,
    topic: str,
    comments: list[str],
) -> ScraperData:
    """Measure sentiment confidence from comments and persist score."""
    logger.info("Running emotional analyzer for topic=%s comments=%d", topic, len(comments))
    positive_hits = 0
    negative_hits = 0

    for comment in comments:
        lowered = comment.lower()
        positive_hits += sum(1 for term in POSITIVE_TERMS if term in lowered)
        negative_hits += sum(1 for term in NEGATIVE_TERMS if term in lowered)

    total_hits = positive_hits + negative_hits
    sentiment_balance = (
        (positive_hits - negative_hits) / total_hits if total_hits > 0 else 0.0
    )
    sentiment_score = clamp_score((sentiment_balance + 1.0) / 2.0)

    payload = {
        "feature": "emotional_intelligence",
        "comments_analyzed": len(comments),
        "positive_hits": positive_hits,
        "negative_hits": negative_hits,
        "sentiment_balance": sentiment_balance,
        "sentiment_score": sentiment_score,
    }
    logger.debug("Emotional intelligence payload=%s", payload)
    return persist_scraper_result(
        db,
        source="emotional_intelligence",
        topic=topic,
        intent_score=sentiment_score,
        payload=payload,
    )
