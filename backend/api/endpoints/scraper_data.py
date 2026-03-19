from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.schemas import ScraperDataCreate, ScraperDataRead
from core.database import get_db
from services.scraper_service import create_scraper_data, list_scraper_data

router = APIRouter()


@router.post("/", response_model=ScraperDataRead, status_code=status.HTTP_201_CREATED)
def create_scraper_data_endpoint(
    payload: ScraperDataCreate,
    db: Session = Depends(get_db),
) -> ScraperDataRead:
    data = create_scraper_data(db, payload)
    return ScraperDataRead.model_validate(data)


@router.get("/", response_model=list[ScraperDataRead])
def list_scraper_data_endpoint(db: Session = Depends(get_db)) -> list[ScraperDataRead]:
    rows = list_scraper_data(db)
    return [ScraperDataRead.model_validate(row) for row in rows]
