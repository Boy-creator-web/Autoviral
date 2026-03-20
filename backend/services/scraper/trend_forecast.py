"""Trend Forecasting feature implementation."""

from __future__ import annotations

import logging
import math
from statistics import mean, pstdev

from sqlalchemy.orm import Session

from models.scraper_data import ScraperData
from services.scraper.common import clamp_score, persist_scraper_result

logger = logging.getLogger(__name__)


def run_trend_forecast(
    db: Session,
    *,
    topic: str,
    trend_points: list[float],
) -> ScraperData:
    """Forecast trend momentum from numeric data points and persist it."""
    logger.info(
        "Running trend forecasting for topic=%s points=%d",
        topic,
        len(trend_points),
    )
    if len(trend_points) < 2:
        slope = 0.0
        volatility = 0.0
        average = float(trend_points[0]) if trend_points else 0.0
    else:
        slope = (trend_points[-1] - trend_points[0]) / (len(trend_points) - 1)
        volatility = pstdev(trend_points)
        average = mean(trend_points)

    slope_score = 0.5 + (math.atan(slope) / math.pi)
    volatility_penalty = clamp_score(volatility / (abs(average) + 1.0))
    trend_strength = clamp_score((slope_score * 0.8) + ((1.0 - volatility_penalty) * 0.2))

    payload = {
        "feature": "trend_forecasting",
        "points_analyzed": len(trend_points),
        "average": average,
        "slope": slope,
        "volatility": volatility,
        "trend_strength": trend_strength,
    }
    logger.debug("Trend forecasting payload=%s", payload)
    return persist_scraper_result(
        db,
        source="trend_forecasting",
        topic=topic,
        intent_score=trend_strength,
        payload=payload,
    )
