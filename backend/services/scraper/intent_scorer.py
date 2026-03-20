"""Purchase Intent Scoring feature implementation."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from models.scraper_data import ScraperData
from services.scraper.common import clamp_score, persist_scraper_result

logger = logging.getLogger(__name__)

PURCHASE_SIGNAL_WEIGHTS = {
    "buy": 0.30,
    "purchase": 0.30,
    "order": 0.25,
    "quote": 0.22,
    "budget": 0.16,
    "invoice": 0.22,
    "contract": 0.20,
    "implementation": 0.14,
    "migration": 0.14,
    "decision_maker": 0.18,
}


def run_purchase_intent_scoring(
    db: Session,
    *,
    topic: str,
    lead_signals: list[str],
) -> ScraperData:
    """Calculate purchase intent score from lead qualification signals."""
    logger.info(
        "Running purchase intent scoring topic=%s lead_signals=%d",
        topic,
        len(lead_signals),
    )
    total_score = 0.0
    matched_signals: list[str] = []

    for signal in lead_signals:
        lowered = signal.lower()
        for keyword, weight in PURCHASE_SIGNAL_WEIGHTS.items():
            if keyword in lowered:
                total_score += weight
                matched_signals.append(signal)
                break

    intent_score = clamp_score(total_score / max(0.4, len(lead_signals) * 0.22))
    payload = {
        "feature": "purchase_intent_scoring",
        "lead_signals_analyzed": len(lead_signals),
        "matched_signals": matched_signals,
        "raw_weighted_score": total_score,
        "intent_score": intent_score,
    }
    logger.debug("Purchase intent payload=%s", payload)
    return persist_scraper_result(
        db,
        source="purchase_intent_scoring",
        topic=topic,
        intent_score=intent_score,
        payload=payload,
    )
