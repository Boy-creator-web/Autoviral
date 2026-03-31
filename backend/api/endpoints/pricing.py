"""Pricing plans endpoint."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends

from core.database import get_db
from models.pricing_plan import PricingPlan
from schemas.billing import PricingPlanRead

router = APIRouter()


DEFAULT_PLANS = [
    {
        "code": "starter",
        "name": "Starter",
        "description": "Untuk mulai campaign awal",
        "price_monthly": 299000.0,
        "video_quota": 20,
        "campaign_quota": 5,
        "scraper_quota": 50,
    },
    {
        "code": "growth",
        "name": "Growth",
        "description": "Untuk tim marketing berkembang",
        "price_monthly": 799000.0,
        "video_quota": 80,
        "campaign_quota": 20,
        "scraper_quota": 250,
    },
    {
        "code": "scale",
        "name": "Scale",
        "description": "Untuk operasi skala besar",
        "price_monthly": 1999000.0,
        "video_quota": 300,
        "campaign_quota": 80,
        "scraper_quota": 1000,
    },
]


def ensure_default_plans(db: Session) -> None:
    existing_codes = set(db.scalars(select(PricingPlan.code)).all())
    for item in DEFAULT_PLANS:
        if item["code"] in existing_codes:
            continue
        db.add(PricingPlan(**item, active=True))
    db.commit()


@router.get("/", response_model=list[PricingPlanRead])
def list_pricing(db: Session = Depends(get_db)) -> list[PricingPlanRead]:
    ensure_default_plans(db)
    rows = list(db.scalars(select(PricingPlan).where(PricingPlan.active.is_(True)).order_by(PricingPlan.price_monthly)).all())
    return [
        PricingPlanRead(
            id=row.id,
            code=row.code,
            name=row.name,
            description=row.description,
            price_monthly=row.price_monthly,
            video_quota=row.video_quota,
            campaign_quota=row.campaign_quota,
            scraper_quota=row.scraper_quota,
            active=row.active,
        )
        for row in rows
    ]
