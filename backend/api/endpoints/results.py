"""Campaign results endpoint."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException, status

from core.database import get_db
from models.campaign_action import CampaignAction
from models.campaign_result import CampaignResult
from schemas.operations import CampaignResultCreate, CampaignResultRead

router = APIRouter()


@router.get("/", response_model=list[CampaignResultRead])
def list_results(db: Session = Depends(get_db)) -> list[CampaignResultRead]:
    rows = list(db.scalars(select(CampaignResult).order_by(CampaignResult.id.desc())).all())
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
def create_result(payload: CampaignResultCreate, db: Session = Depends(get_db)) -> CampaignResultRead:
    action = db.get(CampaignAction, payload.action_id)
    if action is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign action not found")

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
