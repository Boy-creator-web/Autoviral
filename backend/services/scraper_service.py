import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.schemas import ScraperDataCreate
from models.scraper_data import ScraperData


def create_scraper_data(db: Session, payload: ScraperDataCreate) -> ScraperData:
    row = ScraperData(
        source=payload.source,
        topic=payload.topic,
        intent_score=payload.intent_score,
        raw_data=payload.raw_data,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_scraper_data(db: Session, source: str | None = None) -> list[ScraperData]:
    statement = select(ScraperData).order_by(ScraperData.id)
    if source is not None:
        statement = statement.where(ScraperData.source == source)
    return list(db.scalars(statement).all())


def create_scraper_data_from_engine(
    db: Session,
    source: str,
    topic: str,
    intent_score: float,
    raw_data: dict,
) -> ScraperData:
    row = ScraperData(
        source=source,
        topic=topic,
        intent_score=intent_score,
        raw_data=json.dumps(raw_data, ensure_ascii=False),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
