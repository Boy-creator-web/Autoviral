"""Competitor Death Watch feature implementation."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from models.scraper_data import ScraperData
from services.scraper.common import persist_scraper_result

logger = logging.getLogger(__name__)

RISK_KEYWORDS = {
    "shutdown",
    "layoff",
    "bankrupt",
    "bankruptcy",
    "lawsuit",
    "breach",
    "recall",
    "churn",
}


def run_competitor_death_watch(
    db: Session,
    *,
    topic: str,
    competitor_signals: list[str],
) -> ScraperData:
    """Detect competitor weakness signals and persist opportunity score."""
    logger.info(
        "Running competitor death watch for topic=%s signal_count=%d",
        topic,
        len(competitor_signals),
    )
    lowered_signals = [signal.lower() for signal in competitor_signals]
    matched_signals = [
        signal
        for signal in competitor_signals
        if any(keyword in signal.lower() for keyword in RISK_KEYWORDS)
    ]
    risk_ratio = len(matched_signals) / max(1, len(lowered_signals))
    opportunity_score = 0.35 + (risk_ratio * 0.65)

    payload = {
        "feature": "competitor_death_watch",
        "signals_analyzed": len(competitor_signals),
        "risk_hits": len(matched_signals),
        "risk_ratio": risk_ratio,
        "matched_signals": matched_signals,
        "opportunity_score": opportunity_score,
    }
    logger.debug("Competitor death watch payload=%s", payload)
    return persist_scraper_result(
        db,
        source="competitor_death_watch",
        topic=topic,
        intent_score=opportunity_score,
        payload=payload,
    )
