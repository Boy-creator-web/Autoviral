"""Emotional Intelligence feature implementation."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from models.scraper_data import ScraperData
from services.scraper.common import clamp_score, persist_scraper_result

logger = logging.getLogger(__name__)

EMOTION_KEYWORDS = {
    "frustrasi": {"frustrated", "annoyed", "angry", "not working", "broken", "stuck"},
    "penasaran": {"curious", "wondering", "interesting", "how does", "can it"},
    "khawatir": {"worried", "risk", "unsafe", "concerned", "afraid", "fear"},
    "antusias": {"excited", "love", "great", "amazing", "can't wait", "awesome"},
    "kecewa": {"disappointed", "regret", "waste", "let down", "not worth"},
    "bingung": {"confused", "unclear", "complicated", "hard to understand", "what?"},
}

EMOTION_STRATEGY = {
    "frustrasi": "Prioritaskan empati + troubleshooting step-by-step dan berikan SLA penyelesaian.",
    "penasaran": "Berikan edukasi ringkas, demo use-case nyata, lalu CTA eksplorasi produk.",
    "khawatir": "Tonjolkan bukti keamanan/garansi, social proof, dan opsi minim risiko.",
    "antusias": "Percepat ke konversi dengan promo terbatas, onboarding cepat, dan next step jelas.",
    "kecewa": "Lakukan recovery trust: akui masalah, jelaskan perbaikan, tawarkan kompensasi.",
    "bingung": "Sederhanakan pesan, gunakan FAQ visual, dan beri rekomendasi aksi tunggal.",
}


def _detect_emotions(comments: list[str]) -> tuple[dict[str, int], list[dict[str, str]]]:
    counts = {emotion: 0 for emotion in EMOTION_KEYWORDS}
    tagged_examples: list[dict[str, str]] = []
    for comment in comments:
        lowered = comment.lower()
        matched = False
        for emotion, keywords in EMOTION_KEYWORDS.items():
            if any(keyword in lowered for keyword in keywords):
                counts[emotion] += 1
                if len(tagged_examples) < 25:
                    tagged_examples.append({"emotion": emotion, "text": comment})
                matched = True
                break
        if not matched and len(tagged_examples) < 25:
            tagged_examples.append({"emotion": "unknown", "text": comment})
    return counts, tagged_examples


def run_emotional_intelligence(
    db: Session,
    *,
    topic: str,
    comments: list[str],
) -> ScraperData:
    """Detect audience emotions and produce response strategy insight."""
    logger.info("Running emotional analyzer for topic=%s comments=%d", topic, len(comments))
    emotion_counts, tagged_examples = _detect_emotions(comments)
    dominant_emotion = (
        max(emotion_counts.items(), key=lambda item: item[1])[0] if emotion_counts else "bingung"
    )
    dominant_count = emotion_counts.get(dominant_emotion, 0)
    emotion_confidence = clamp_score(dominant_count / max(1, len(comments)))

    payload = {
        "feature": "emotional_intelligence",
        "comments_analyzed": len(comments),
        "emotion_counts": emotion_counts,
        "dominant_emotion": dominant_emotion,
        "emotion_confidence": emotion_confidence,
        "response_strategy": EMOTION_STRATEGY.get(dominant_emotion, EMOTION_STRATEGY["bingung"]),
        "tagged_examples": tagged_examples,
    }
    logger.debug("Emotional intelligence payload=%s", payload)
    return persist_scraper_result(
        db,
        source="emotional_intelligence",
        topic=topic,
        intent_score=emotion_confidence,
        payload=payload,
    )
