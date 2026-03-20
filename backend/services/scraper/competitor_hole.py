"""Deep Competitor Hole feature implementation."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from models.scraper_data import ScraperData
from services.scraper.common import clamp_score, persist_scraper_result

logger = logging.getLogger(__name__)


def run_deep_competitor_hole(
    db: Session,
    *,
    topic: str,
    competitor_contents: list[str],
    pain_points: list[str],
) -> ScraperData:
    """Find market gaps where user pain points are underserved by competitors."""
    logger.info(
        "Running deep competitor hole topic=%s competitor_docs=%d pain_points=%d",
        topic,
        len(competitor_contents),
        len(pain_points),
    )
    merged_competitor_text = " ".join(competitor_contents).lower()
    uncovered_pain_points = [
        point for point in pain_points if point.lower() not in merged_competitor_text
    ]
    coverage_gap = len(uncovered_pain_points) / max(1, len(pain_points))
    gap_score = clamp_score(coverage_gap)

    payload = {
        "feature": "deep_competitor_hole",
        "competitor_docs": len(competitor_contents),
        "pain_points_total": len(pain_points),
        "pain_points_uncovered": uncovered_pain_points,
        "coverage_gap": coverage_gap,
        "gap_score": gap_score,
    }
    logger.debug("Deep competitor hole payload=%s", payload)
    return persist_scraper_result(
        db,
        source="deep_competitor_hole",
        topic=topic,
        intent_score=gap_score,
        payload=payload,
    )
