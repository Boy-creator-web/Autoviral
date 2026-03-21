"""Deep Competitor Hole feature implementation."""

from __future__ import annotations

import logging
import re

from sqlalchemy.orm import Session

from models.scraper_data import ScraperData
from services.scraper.common import clamp_score, persist_scraper_result

logger = logging.getLogger(__name__)

COMPETITOR_WEAKNESS_KEYWORDS = {
    "expensive",
    "slow",
    "poor support",
    "limited",
    "bug",
    "hard to use",
    "not scalable",
    "downtime",
    "missing feature",
}


def _normalize_topic(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"[^a-z0-9\s]", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered).strip()
    return lowered


def run_deep_competitor_hole(
    db: Session,
    *,
    topic: str,
    competitor_contents: list[str],
    audience_questions: list[str],
    pain_points: list[str],
) -> ScraperData:
    """Find topic gaps, unanswered questions, and competitor weaknesses."""
    logger.info(
        "Running deep competitor hole topic=%s competitor_docs=%d questions=%d pain_points=%d",
        topic,
        len(competitor_contents),
        len(audience_questions),
        len(pain_points),
    )
    merged_competitor_text = " ".join(competitor_contents).lower()

    missed_topics = [
        point for point in pain_points if _normalize_topic(point) not in _normalize_topic(merged_competitor_text)
    ]
    unanswered_questions = [
        question
        for question in audience_questions
        if _normalize_topic(question) not in _normalize_topic(merged_competitor_text)
    ]
    weakness_mentions = [
        snippet
        for snippet in competitor_contents
        if any(keyword in snippet.lower() for keyword in COMPETITOR_WEAKNESS_KEYWORDS)
    ]

    uncovered_pain_points = [
        point for point in pain_points if point.lower() not in merged_competitor_text
    ]
    coverage_gap = len(uncovered_pain_points) / max(1, len(pain_points))
    unanswered_ratio = len(unanswered_questions) / max(1, len(audience_questions))
    weakness_ratio = len(weakness_mentions) / max(1, len(competitor_contents))
    gap_score = clamp_score((coverage_gap * 0.5) + (unanswered_ratio * 0.35) + (weakness_ratio * 0.15))

    payload = {
        "feature": "deep_competitor_hole",
        "competitor_docs": len(competitor_contents),
        "audience_questions_total": len(audience_questions),
        "pain_points_total": len(pain_points),
        "pain_points_uncovered": uncovered_pain_points,
        "missed_topics": missed_topics,
        "unanswered_questions": unanswered_questions,
        "competitor_weakness_signals": weakness_mentions[:25],
        "coverage_gap": coverage_gap,
        "unanswered_ratio": unanswered_ratio,
        "weakness_ratio": weakness_ratio,
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
