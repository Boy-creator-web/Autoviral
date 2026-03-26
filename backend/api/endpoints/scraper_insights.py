from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.schemas import ScraperInsightGenerateResponse, ScraperInsightRead, ScraperInsightRequest
from core.database import get_db
from services.scraper.engine import generate_and_store_insights
from services.scraper_service import list_scraper_data

router = APIRouter()


@router.post(
    "/insights",
    response_model=ScraperInsightGenerateResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_scraper_insights_endpoint(
    payload: ScraperInsightRequest,
    db: Session = Depends(get_db),
) -> ScraperInsightGenerateResponse:
    return ScraperInsightGenerateResponse.model_validate(
        generate_and_store_insights(
            db=db,
            seed_text=payload.seed_text,
            product_data=payload.product_data,
        )
    )


@router.get("/insights", response_model=list[ScraperInsightRead])
def list_scraper_insights_endpoint(db: Session = Depends(get_db)) -> list[ScraperInsightRead]:
    rows = list_scraper_data(db, source="mirofish")
    return [ScraperInsightRead.model_validate(row) for row in rows]
