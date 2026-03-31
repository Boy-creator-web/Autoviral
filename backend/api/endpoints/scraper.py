"""Scraper endpoint for intelligence data."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException, status

from core.database import get_db
from models.scraper_data import ScraperData
from models.user import User
from schemas.scraper_data import ScraperDataCreate, ScraperDataRead

router = APIRouter()


@router.get("/", response_model=list[ScraperDataRead])
def list_scraper(db: Session = Depends(get_db)) -> list[ScraperDataRead]:
    rows = list(db.scalars(select(ScraperData).order_by(ScraperData.id.desc())).all())
    return [
        ScraperDataRead(
            id=row.id,
            user_id=row.user_id,
            topic=row.topic,
            source=row.source,
            insight=row.insight,
            status=row.status,
        )
        for row in rows
    ]


@router.post("/", response_model=ScraperDataRead, status_code=status.HTTP_201_CREATED)
def run_scraper(payload: ScraperDataCreate, db: Session = Depends(get_db)) -> ScraperDataRead:
    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    row = ScraperData(
        user_id=payload.user_id,
        topic=payload.topic,
        source=payload.source,
        insight=payload.insight,
        status="ready",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return ScraperDataRead(
        id=row.id,
        user_id=row.user_id,
        topic=row.topic,
        source=row.source,
        insight=row.insight,
        status=row.status,
    )
