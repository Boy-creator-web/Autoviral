"""Utilities shared across scraper feature modules."""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from models.scraper_data import ScraperData

logger = logging.getLogger(__name__)


def clamp_score(value: float) -> float:
    """Normalize score into the 0..1 range."""
    return max(0.0, min(1.0, float(value)))


def persist_scraper_result(
    db: Session,
    *,
    source: str,
    topic: str,
    intent_score: float,
    payload: dict[str, Any],
) -> ScraperData:
    """Persist a scraper feature output into ScraperData."""
    normalized_score = clamp_score(intent_score)
    row = ScraperData(
        source=source,
        topic=topic,
        intent_score=normalized_score,
        raw_data=json.dumps(payload, ensure_ascii=True),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    logger.debug(
        "Saved scraper result source=%s topic=%s score=%.3f id=%s",
        source,
        topic,
        normalized_score,
        row.id,
    )
    return row
