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

BUYING_INTENT_TERMS = {
    "price",
    "pricing",
    "discount",
    "ready to buy",
    "buy now",
    "purchase",
    "checkout",
    "order",
    "invoice",
}

PHASE_KEYWORDS = {
    "research": {"how", "what is", "guide", "learn", "explore", "research"},
    "comparison": {"vs", "compare", "alternative", "difference", "better than"},
    "validation": {"review", "case study", "testimonial", "proof", "trust"},
    "purchase": {"buy", "checkout", "order", "invoice", "pricing", "payment"},
    "urgency": {"today", "now", "urgent", "asap", "immediately", "deadline"},
}


def _detect_phase_counts(signals: list[str]) -> dict[str, int]:
    counts = {phase: 0 for phase in PHASE_KEYWORDS}
    for signal in signals:
        lowered = signal.lower()
        for phase, keywords in PHASE_KEYWORDS.items():
            if any(keyword in lowered for keyword in keywords):
                counts[phase] += 1
    return counts


def run_micro_conversion_signal(
    db: Session,
    *,
    topic: str,
    user_actions: list[str],
    user_text_signals: list[str],
) -> ScraperData:
    """Extract micro-conversion intent and funnel phase from user behavior + text."""
    logger.info(
        "Running micro-conversion detector for topic=%s action_count=%d text_signals=%d",
        topic,
        len(user_actions),
        len(user_text_signals),
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

    buying_intent_hits = [
        signal
        for signal in user_text_signals
        if any(term in signal.lower() for term in BUYING_INTENT_TERMS)
    ]
    text_intent_score = clamp_score(len(buying_intent_hits) / max(1.0, len(user_text_signals) * 0.4))

    phase_counts = _detect_phase_counts(user_text_signals + user_actions)
    dominant_phase = max(phase_counts.items(), key=lambda item: item[1])[0] if phase_counts else "research"
    phase_confidence = clamp_score(
        phase_counts.get(dominant_phase, 0) / max(1.0, len(user_text_signals) + len(user_actions))
    )

    normalized_intent = clamp_score(
        (weighted_score / max(1.0, (len(user_actions) * 0.25))) * 0.55
        + (text_intent_score * 0.3)
        + (phase_confidence * 0.15)
    )
    payload = {
        "feature": "micro_conversion_signal",
        "actions_analyzed": len(user_actions),
        "text_signals_analyzed": len(user_text_signals),
        "matched_actions": matched_actions,
        "buying_intent_hits": buying_intent_hits[:30],
        "weighted_score": weighted_score,
        "text_intent_score": text_intent_score,
        "phase_counts": phase_counts,
        "dominant_phase": dominant_phase,
        "phase_confidence": phase_confidence,
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
