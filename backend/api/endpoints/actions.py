"""Campaign action endpoint for operational actions."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from core.audit import audit_log
from core.database import get_db
from core.rate_limit import apply_rate_limit_headers, enforce_ip_rate_limit, enforce_user_rate_limit
from core.security import get_current_user
from models.campaign_action import CampaignAction
from models.user import User
from schemas.operations import CampaignActionCreate, CampaignActionRead

router = APIRouter()


@router.get("/", response_model=list[CampaignActionRead])
def list_actions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CampaignActionRead]:
    rows = list(db.scalars(select(CampaignAction).order_by(CampaignAction.id.desc())).all())
    if current_user.role != "admin":
        rows = [row for row in rows if row.user_id == current_user.id]
    return [
        CampaignActionRead(
            id=row.id,
            user_id=row.user_id,
            action_type=row.action_type,
            title=row.title,
            payload=row.payload,
            status=row.status,
        )
        for row in rows
    ]


@router.post("/", response_model=CampaignActionRead, status_code=status.HTTP_201_CREATED)
def create_action(
    payload: CampaignActionCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CampaignActionRead:
    ip_limit = enforce_ip_rate_limit(request)
    user_limit = enforce_user_rate_limit(current_user.id)
    apply_rate_limit_headers(response, ip_limit, user_limit)
    if current_user.role != "admin" and current_user.id != payload.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed for this user")

    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    row = CampaignAction(
        user_id=payload.user_id,
        action_type=payload.action_type,
        title=payload.title,
        payload=payload.payload,
        status="running",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    audit_log(
        "campaign_action_created",
        actor=f"user:{current_user.id}",
        target=f"action:{row.id}",
        metadata={"action_type": row.action_type, "owner_user_id": row.user_id},
        db=db,
    )
    return CampaignActionRead(
        id=row.id,
        user_id=row.user_id,
        action_type=row.action_type,
        title=row.title,
        payload=row.payload,
        status=row.status,
    )
