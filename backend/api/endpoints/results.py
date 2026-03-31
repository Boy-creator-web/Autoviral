"""Campaign results endpoint."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException, status

from core.database import get_db
from core.security import get_current_user
from models.campaign_action import CampaignAction
from models.campaign_result import CampaignResult
from models.user import User
from schemas.operations import CampaignResultCreate, CampaignResultRead

router = APIRouter()


@router.get("/", response_model=list[CampaignResultRead])
def list_results(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CampaignResultRead]:
    rows = list(db.scalars(select(CampaignResult).order_by(CampaignResult.id.desc())).all())
    if current_user.role != "admin":
        allowed_action_ids = set(
            db.scalars(select(CampaignAction.id).where(CampaignAction.user_id == current_user.id)).all()
        )
        rows = [row for row in rows if row.action_id in allowed_action_ids]
    return [
        CampaignResultRead(
            id=row.id,
            action_id=row.action_id,
            summary=row.summary,
            result_data=row.result_data,
            status=row.status,
        )
        for row in rows
    ]


@router.post("/", response_model=CampaignResultRead, status_code=status.HTTP_201_CREATED)
def create_result(
    payload: CampaignResultCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CampaignResultRead:
    action = db.get(CampaignAction, payload.action_id)
    if action is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign action not found")
    if current_user.role != "admin" and current_user.id != action.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed for this action")

    row = CampaignResult(
        action_id=payload.action_id,
        summary=payload.summary,
        result_data=payload.result_data,
        status="completed",
    )
    action.status = "completed"
    db.add(action)
    db.add(row)
    db.commit()
    db.refresh(row)
    return CampaignResultRead(
        id=row.id,
        action_id=row.action_id,
        summary=row.summary,
        result_data=row.result_data,
        status=row.status,
    )
