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


def list_scraper_data(db: Session) -> list[ScraperData]:
    return list(db.scalars(select(ScraperData).order_by(ScraperData.id)).all())
