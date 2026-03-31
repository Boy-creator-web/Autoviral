"""Combined operation status and dashboard summary endpoint."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends

from core.database import get_db
from core.security import get_admin_user
from models.campaign_action import CampaignAction
from models.campaign_report import CampaignReport
from models.campaign_result import CampaignResult
from models.payment import Payment
from models.subscription import Subscription
from models.user import User

router = APIRouter()


@router.get("/summary", dependencies=[Depends(get_admin_user)])
def get_summary(db: Session = Depends(get_db)) -> dict[str, object]:
    users = db.scalar(select(func.count(User.id))) or 0
    subscriptions = db.scalar(select(func.count(Subscription.id))) or 0
    paid = db.scalar(select(func.count(Payment.id)).where(Payment.status == "paid")) or 0
    actions = db.scalar(select(func.count(CampaignAction.id))) or 0
    results = db.scalar(select(func.count(CampaignResult.id))) or 0
    reports = db.scalar(select(func.count(CampaignReport.id))) or 0

    return {
        "message": "ok",
        "data": {
            "users": users,
            "subscriptions": subscriptions,
            "paid_transactions": paid,
            "actions": actions,
            "results": results,
            "reports": reports,
        },
    }
