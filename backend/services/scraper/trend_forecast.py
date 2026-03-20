"""Trend Forecasting feature implementation."""

from __future__ import annotations

import logging
import math
from statistics import mean, pstdev

from sqlalchemy.orm import Session

from models.scraper_data import ScraperData
from services.scraper.common import clamp_score, persist_scraper_result

logger = logging.getLogger(__name__)

EARLY_SIGNAL_KEYWORDS = {
    "anyone tried",
    "new",
    "beta",
    "launch",
    "trending",
    "underrated",
    "just discovered",
    "what is",
    "worth it",
}

SHARE_KEYWORDS = {"share", "retweet", "repost", "send to", "viral", "recommend"}
ACTION_KEYWORDS = {"buy", "join", "subscribe", "signup", "register", "try"}


def run_trend_forecast(
    db: Session,
    *,
    topic: str,
    trend_points: list[float],
    forum_signals: list[str],
) -> ScraperData:
    """Forecast trend timing, strength, and virality from signals."""
    logger.info(
        "Running trend forecasting for topic=%s points=%d forum_signals=%d",
        topic,
        len(trend_points),
        len(forum_signals),
    )
    if len(trend_points) < 2:
        slope = 0.0
        volatility = 0.0
        average = float(trend_points[0]) if trend_points else 0.0
        acceleration = 0.0
    else:
        slope = (trend_points[-1] - trend_points[0]) / (len(trend_points) - 1)
        volatility = pstdev(trend_points)
        average = mean(trend_points)
        first_delta = trend_points[1] - trend_points[0]
        last_delta = trend_points[-1] - trend_points[-2]
        acceleration = last_delta - first_delta

    slope_score = 0.5 + (math.atan(slope) / math.pi)
    acceleration_score = clamp_score(0.5 + (math.atan(acceleration) / math.pi))
    volatility_penalty = clamp_score(volatility / (abs(average) + 1.0))
    trend_strength = clamp_score(
        (slope_score * 0.65) + (acceleration_score * 0.2) + ((1.0 - volatility_penalty) * 0.15)
    )

    early_forum_hits = [
        signal
        for signal in forum_signals
        if any(keyword in signal.lower() for keyword in EARLY_SIGNAL_KEYWORDS)
    ]
    early_signal_score = clamp_score(len(early_forum_hits) / max(1.0, len(forum_signals) * 0.45))

    share_hits = 0
    action_hits = 0
    for signal in forum_signals:
        lowered = signal.lower()
        if any(keyword in lowered for keyword in SHARE_KEYWORDS):
            share_hits += 1
        if any(keyword in lowered for keyword in ACTION_KEYWORDS):
            action_hits += 1

    viral_coefficient = clamp_score((share_hits * 0.7 + action_hits * 0.3) / max(1.0, len(forum_signals) * 0.6))

    if slope <= 0:
        predicted_peak_index = max(0, len(trend_points) - 1)
    else:
        growth_buffer = max(0.0, 1.0 - volatility_penalty)
        projected_steps = int(round((2.5 * growth_buffer) + (2.0 * acceleration_score)))
        predicted_peak_index = max(0, len(trend_points) - 1 + projected_steps)

    payload = {
        "feature": "trend_forecasting",
        "points_analyzed": len(trend_points),
        "forum_signals_analyzed": len(forum_signals),
        "early_signal_hits": len(early_forum_hits),
        "early_signal_score": early_signal_score,
        "average": average,
        "slope": slope,
        "acceleration": acceleration,
        "volatility": volatility,
        "predicted_peak_index": predicted_peak_index,
        "viral_coefficient": viral_coefficient,
        "trend_strength": trend_strength,
        "early_signals": early_forum_hits[:25],
    }
    logger.debug("Trend forecasting payload=%s", payload)
    return persist_scraper_result(
        db,
        source="trend_forecasting",
        topic=topic,
        intent_score=trend_strength,
        payload=payload,
    )
