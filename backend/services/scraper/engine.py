from typing import Any

from sqlalchemy.orm import Session

from services.mirofish_client import generate_insights, predict_trends, simulate_audience
from services.scraper_service import create_scraper_data_from_engine


def generate_and_store_insights(
    db: Session,
    seed_text: str,
    product_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    trends = predict_trends(seed_text)
    audience = simulate_audience(product_data or {"seed_text": seed_text})
    summary = generate_insights()

    payload = {
        "seed_text": seed_text,
        "trends": trends,
        "audience": audience,
        "summary": summary,
    }
    row = create_scraper_data_from_engine(
        db,
        source="mirofish",
        topic=seed_text,
        intent_score=0.9,
        raw_data=payload,
    )
    return {
        "id": row.id,
        "source": row.source,
        "topic": row.topic,
        "intent_score": row.intent_score,
        "raw_data": row.raw_data,
    }

