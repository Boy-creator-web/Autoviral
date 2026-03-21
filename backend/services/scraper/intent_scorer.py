"""Purchase Intent Scoring feature implementation."""

from __future__ import annotations

import logging
import re

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

ACTIVITY_SIGNAL_WEIGHTS = {
    "view_pricing": 0.18,
    "repeat_visit": 0.12,
    "watch_demo": 0.16,
    "download_brochure": 0.14,
    "contact_sales": 0.24,
    "request_quote": 0.24,
    "book_call": 0.22,
    "checkout_start": 0.26,
    "add_to_cart": 0.22,
}


def _extract_user_id(activity_line: str) -> str:
    match = re.search(r"user[:=_\- ]+([a-zA-Z0-9]+)", activity_line, flags=re.IGNORECASE)
    if match:
        return match.group(1)
    return "unknown"


def run_purchase_intent_scoring(
    db: Session,
    *,
    topic: str,
    lead_signals: list[str],
    user_activity_logs: list[str],
) -> ScraperData:
    """Calculate 0-100 purchase intent and identify high-intent users."""
    logger.info(
        "Running purchase intent scoring topic=%s lead_signals=%d activity_logs=%d",
        topic,
        len(lead_signals),
        len(user_activity_logs),
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

    activity_score = 0.0
    user_scores: dict[str, float] = {}
    for line in user_activity_logs:
        lowered = line.lower()
        user_id = _extract_user_id(line)
        for keyword, weight in ACTIVITY_SIGNAL_WEIGHTS.items():
            if keyword in lowered:
                activity_score += weight
                user_scores[user_id] = user_scores.get(user_id, 0.0) + weight
                break

    normalized_lead_score = clamp_score(total_score / max(0.4, len(lead_signals) * 0.22))
    normalized_activity_score = clamp_score(
        activity_score / max(0.4, len(user_activity_logs) * 0.22)
    )
    intent_score = clamp_score((normalized_lead_score * 0.58) + (normalized_activity_score * 0.42))
    intent_score_0_100 = round(intent_score * 100, 2)

    high_intent_users = [
        {"user_id": user_id, "intent_score": round(clamp_score(score / 0.8) * 100, 2)}
        for user_id, score in sorted(user_scores.items(), key=lambda item: item[1], reverse=True)
        if clamp_score(score / 0.8) * 100 >= 70
    ]
    payload = {
        "feature": "purchase_intent_scoring",
        "lead_signals_analyzed": len(lead_signals),
        "user_activity_logs_analyzed": len(user_activity_logs),
        "matched_signals": matched_signals,
        "raw_weighted_score": total_score,
        "activity_weighted_score": activity_score,
        "normalized_lead_score": normalized_lead_score,
        "normalized_activity_score": normalized_activity_score,
        "intent_score": intent_score,
        "intent_score_0_100": intent_score_0_100,
        "high_intent_users": high_intent_users[:50],
    }
    logger.debug("Purchase intent payload=%s", payload)
    return persist_scraper_result(
        db,
        source="purchase_intent_scoring",
        topic=topic,
        intent_score=intent_score,
        payload=payload,
    )
