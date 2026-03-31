"""Subscriptions endpoint for user registrations to plans."""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from core.audit import audit_log
from core.database import get_db
from core.rate_limit import apply_rate_limit_headers, enforce_ip_rate_limit, enforce_user_rate_limit
from core.security import get_current_user
from models.pricing_plan import PricingPlan
from models.subscription import Subscription
from models.user import User
from schemas.billing import SubscriptionCreate, SubscriptionRead

router = APIRouter()


@router.get("/", response_model=list[SubscriptionRead])
def list_subscriptions(db: Session = Depends(get_db)) -> list[SubscriptionRead]:
    rows = list(db.scalars(select(Subscription).order_by(Subscription.id.desc())).all())
    return [
        SubscriptionRead(
            id=row.id,
            user_id=row.user_id,
            plan_id=row.plan_id,
            status=row.status,
            start_date=row.start_date,
            end_date=row.end_date,
        )
        for row in rows
    ]


@router.post("/", response_model=SubscriptionRead, status_code=status.HTTP_201_CREATED)
def create_subscription(
    payload: SubscriptionCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SubscriptionRead:
    ip_limit = enforce_ip_rate_limit(request)
    user_limit = enforce_user_rate_limit(current_user.id)
    apply_rate_limit_headers(response, ip_limit, user_limit)
    if current_user.role != "admin" and current_user.id != payload.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed for this user")

    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    plan = db.get(PricingPlan, payload.plan_id)
    if plan is None or not plan.active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pricing plan not found")

    start = date.today()
    end = start + timedelta(days=30 * payload.months)

    row = Subscription(
        user_id=payload.user_id,
        plan_id=payload.plan_id,
        status="pending",
        start_date=start.isoformat(),
        end_date=end.isoformat(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    audit_log(
        "subscription_created",
        actor=f"user:{current_user.id}",
        target=f"subscription:{row.id}",
        metadata={"plan_id": row.plan_id, "months": payload.months},
        db=db,
    )
    return SubscriptionRead(
        id=row.id,
        user_id=row.user_id,
        plan_id=row.plan_id,
        status=row.status,
        start_date=row.start_date,
        end_date=row.end_date,
    )
