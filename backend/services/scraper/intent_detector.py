"""Micro-Conversion Signal feature implementation."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from models.scraper_data import ScraperData
from services.scraper.common import clamp_score, persist_scraper_result

logger = logging.getLogger(__name__)

ACTION_WEIGHTS = {
    "signup": 0.18,
    "register": 0.18,
    "trial": 0.22,
    "pricing": 0.20,
    "checkout": 0.25,
    "demo": 0.22,
    "contact_sales": 0.24,
    "add_to_cart": 0.24,
    "subscribe": 0.16,
}


def run_micro_conversion_signal(
    db: Session,
    *,
    topic: str,
    user_actions: list[str],
) -> ScraperData:
    """Extract micro-conversion intent from user actions and persist result."""
    logger.info(
        "Running micro-conversion detector for topic=%s action_count=%d",
        topic,
        len(user_actions),
    )
    lowered_actions = [action.lower() for action in user_actions]
    matched_actions: list[str] = []
    weighted_score = 0.0

    for action in lowered_actions:
        for keyword, weight in ACTION_WEIGHTS.items():
            if keyword in action:
                weighted_score += weight
                matched_actions.append(action)
                break

    normalized_intent = clamp_score(weighted_score / max(1.0, (len(user_actions) * 0.25)))
    payload = {
        "feature": "micro_conversion_signal",
        "actions_analyzed": len(user_actions),
        "matched_actions": matched_actions,
        "weighted_score": weighted_score,
        "normalized_intent": normalized_intent,
    }
    logger.debug("Micro-conversion payload=%s", payload)
    return persist_scraper_result(
        db,
        source="micro_conversion_signal",
        topic=topic,
        intent_score=normalized_intent,
        payload=payload,
    )
