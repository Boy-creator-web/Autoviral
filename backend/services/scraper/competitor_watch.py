"""Competitor Death Watch feature implementation."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from statistics import pstdev

from sqlalchemy.orm import Session

from models.scraper_data import ScraperData
from services.scraper.common import clamp_score, persist_scraper_result

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

NEGATIVE_COMMENT_KEYWORDS = {
    "scam",
    "refund",
    "cancel",
    "cancelled",
    "bad",
    "broken",
    "slow",
    "frustrated",
    "unusable",
    "complaint",
    "issue",
}

DATE_PATTERNS = (
    re.compile(r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\b"),
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
)


def _extract_post_dates(competitor_posts: list[str]) -> list[datetime]:
    dates: list[datetime] = []
    for post in competitor_posts:
        for pattern in DATE_PATTERNS:
            match = pattern.search(post)
            if match is None:
                continue
            raw = match.group(0)
            try:
                if "T" in raw:
                    parsed = datetime.fromisoformat(raw).replace(tzinfo=timezone.utc)
                else:
                    parsed = datetime.strptime(raw, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                dates.append(parsed)
                break
            except ValueError:
                continue
    return sorted(dates)


def run_competitor_death_watch(
    db: Session,
    *,
    topic: str,
    competitor_signals: list[str],
    competitor_videos: list[str],
    competitor_comments: list[str],
    competitor_posts: list[str],
) -> ScraperData:
    """Monitor competitor content weakness and persist opportunity score."""
    logger.info(
        "Running competitor death watch for topic=%s signal_count=%d videos=%d comments=%d posts=%d",
        topic,
        len(competitor_signals),
        len(competitor_videos),
        len(competitor_comments),
        len(competitor_posts),
    )
    all_signals = competitor_signals + competitor_videos
    lowered_signals = [signal.lower() for signal in all_signals]
    matched_signals = [
        signal
        for signal in all_signals
        if any(keyword in signal.lower() for keyword in RISK_KEYWORDS)
    ]

    distressed_comments = [
        comment
        for comment in competitor_comments
        if any(keyword in comment.lower() for keyword in NEGATIVE_COMMENT_KEYWORDS)
    ]

    post_dates = _extract_post_dates(competitor_posts)
    posting_instability = 0.0
    silence_days = 0.0
    if len(post_dates) >= 2:
        intervals = [
            (post_dates[idx] - post_dates[idx - 1]).total_seconds() / 86400
            for idx in range(1, len(post_dates))
        ]
        avg_interval = sum(intervals) / len(intervals)
        interval_spread = pstdev(intervals)
        posting_instability = clamp_score(interval_spread / max(1.0, avg_interval))
        silence_days = (datetime.now(timezone.utc) - post_dates[-1]).total_seconds() / 86400
    elif len(post_dates) == 1:
        silence_days = (datetime.now(timezone.utc) - post_dates[-1]).total_seconds() / 86400

    risk_ratio = len(matched_signals) / max(1, len(lowered_signals))
    comment_pressure = len(distressed_comments) / max(1, len(competitor_comments))
    silence_risk = clamp_score(silence_days / 14.0)
    posting_pattern_risk = clamp_score((posting_instability * 0.6) + (silence_risk * 0.4))
    opportunity_score = clamp_score(
        (risk_ratio * 0.42) + (comment_pressure * 0.34) + (posting_pattern_risk * 0.24)
    )

    payload = {
        "feature": "competitor_death_watch",
        "signals_analyzed": len(all_signals),
        "video_items_analyzed": len(competitor_videos),
        "comments_analyzed": len(competitor_comments),
        "posts_analyzed": len(competitor_posts),
        "risk_hits": len(matched_signals),
        "risk_ratio": risk_ratio,
        "distressed_comment_hits": len(distressed_comments),
        "comment_pressure": comment_pressure,
        "posting_instability": posting_instability,
        "silence_days": silence_days,
        "posting_pattern_risk": posting_pattern_risk,
        "matched_signals": matched_signals,
        "distressed_comments": distressed_comments[:25],
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
