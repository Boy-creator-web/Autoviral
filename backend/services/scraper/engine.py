"""Scraper engine orchestration and insight retrieval."""

from __future__ import annotations

import json
import logging
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.schemas import ScraperAnalyzeRequest
from models.scraper_data import ScraperData
from services.scraper.competitor_hole import run_deep_competitor_hole
from services.scraper.competitor_watch import run_competitor_death_watch
from services.scraper.emotion_analyzer import run_emotional_intelligence
from services.scraper.intent_detector import run_micro_conversion_signal
from services.scraper.intent_scorer import run_purchase_intent_scoring
from services.scraper.trend_forecast import run_trend_forecast

logger = logging.getLogger(__name__)


def run_manual_scraper_analysis(
    db: Session,
    *,
    payload: ScraperAnalyzeRequest,
) -> list[ScraperData]:
    """Execute all scraper intelligence features and persist each result."""
    logger.info("Running scraper engine for topic=%s", payload.topic)
    results = [
        run_competitor_death_watch(
            db,
            topic=payload.topic,
            competitor_signals=payload.competitor_signals,
            competitor_videos=payload.competitor_videos,
            competitor_comments=payload.competitor_comments,
            competitor_posts=payload.competitor_posts,
        ),
        run_trend_forecast(
            db,
            topic=payload.topic,
            trend_points=payload.trend_points,
            forum_signals=payload.forum_signals,
        ),
        run_micro_conversion_signal(
            db,
            topic=payload.topic,
            user_actions=payload.user_actions,
            user_text_signals=payload.user_text_signals,
        ),
        run_emotional_intelligence(
            db,
            topic=payload.topic,
            comments=payload.comments,
        ),
        run_deep_competitor_hole(
            db,
            topic=payload.topic,
            competitor_contents=payload.competitor_contents,
            audience_questions=payload.audience_questions,
            pain_points=payload.pain_points,
        ),
        run_purchase_intent_scoring(
            db,
            topic=payload.topic,
            lead_signals=payload.lead_signals,
            user_activity_logs=payload.user_activity_logs,
        ),
    ]
    logger.info("Scraper engine completed topic=%s saved_rows=%d", payload.topic, len(results))
    return results


def list_scraper_insights(
    db: Session,
    *,
    limit: int = 50,
    topic: str | None = None,
) -> list[ScraperData]:
    """Read latest scraper insights with optional topic filter."""
    statement = select(ScraperData).order_by(ScraperData.id.desc()).limit(limit)
    if topic:
        statement = statement.where(ScraperData.topic == topic)
    return list(db.scalars(statement).all())


def summarize_scraper_insights(
    db: Session,
    *,
    limit: int = 200,
    topic: str | None = None,
) -> dict:
    """Build cross-feature insight summary from persisted ScraperData rows."""
    rows = list_scraper_insights(db, limit=limit, topic=topic)
    by_source: dict[str, dict[str, float | int]] = defaultdict(
        lambda: {"count": 0, "avg_intent_score": 0.0}
    )
    high_intent_users: list[dict[str, str | float]] = []
    missed_topics: list[str] = []
    unanswered_questions: list[str] = []
    emotion_overview: dict[str, int] = defaultdict(int)
    latest_features: list[dict] = []

    for row in rows:
        source_summary = by_source[row.source]
        source_summary["count"] = int(source_summary["count"]) + 1
        running_count = int(source_summary["count"])
        current_avg = float(source_summary["avg_intent_score"])
        source_summary["avg_intent_score"] = (
            ((current_avg * (running_count - 1)) + float(row.intent_score)) / running_count
        )

        parsed_raw: dict = {}
        try:
            parsed_raw = json.loads(row.raw_data)
        except json.JSONDecodeError:
            parsed_raw = {}

        if row.source == "purchase_intent_scoring":
            high_intent_users.extend(parsed_raw.get("high_intent_users", []))
        if row.source == "deep_competitor_hole":
            missed_topics.extend(parsed_raw.get("missed_topics", []))
            unanswered_questions.extend(parsed_raw.get("unanswered_questions", []))
        if row.source == "emotional_intelligence":
            for emotion, count in parsed_raw.get("emotion_counts", {}).items():
                emotion_overview[emotion] += int(count)

        latest_features.append(
            {
                "id": row.id,
                "source": row.source,
                "topic": row.topic,
                "intent_score": row.intent_score,
            }
        )

    deduped_high_intent: dict[str, float] = {}
    for item in high_intent_users:
        user_id = str(item.get("user_id", "unknown"))
        score = float(item.get("intent_score", 0.0))
        deduped_high_intent[user_id] = max(deduped_high_intent.get(user_id, 0.0), score)

    return {
        "topic": topic,
        "total_insights": len(rows),
        "by_source": dict(by_source),
        "high_intent_users": [
            {"user_id": user_id, "intent_score": round(score, 2)}
            for user_id, score in sorted(
                deduped_high_intent.items(), key=lambda item: item[1], reverse=True
            )[:50]
        ],
        "missed_topics": sorted(set(missed_topics))[:100],
        "unanswered_questions": sorted(set(unanswered_questions))[:100],
        "emotion_overview": dict(emotion_overview),
        "latest_features": latest_features[:25],
    }
