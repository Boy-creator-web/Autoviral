"""Campaign action endpoint for operational actions."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException, status

from core.database import get_db
from models.campaign_action import CampaignAction
from models.user import User
from schemas.operations import CampaignActionCreate, CampaignActionRead

router = APIRouter()


@router.get("/", response_model=list[CampaignActionRead])
def list_actions(db: Session = Depends(get_db)) -> list[CampaignActionRead]:
    rows = list(db.scalars(select(CampaignAction).order_by(CampaignAction.id.desc())).all())
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
def create_action(payload: CampaignActionCreate, db: Session = Depends(get_db)) -> CampaignActionRead:
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
    return CampaignActionRead(
        id=row.id,
        user_id=row.user_id,
        action_type=row.action_type,
        title=row.title,
        payload=row.payload,
        status=row.status,
    )
