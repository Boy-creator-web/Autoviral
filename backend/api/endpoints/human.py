"""Synthetic Human Generator API endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.schemas import HumanCreateRequest, HumanTrainRequest, HumanTrainResponse, SyntheticHumanRead
from core.database import get_db
from services.video.synthetic_human import create_human_record, list_human_records, train_human_model

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/create", response_model=SyntheticHumanRead, status_code=status.HTTP_201_CREATED)
async def create_human_endpoint(
    payload: HumanCreateRequest,
    db: Session = Depends(get_db),
) -> SyntheticHumanRead:
    """Create a new synthetic human from prompt and persist to DB."""
    try:
        human = await create_human_record(
            db,
            user_id=payload.user_id,
            name=payload.name,
            age=payload.age,
            gender=payload.gender,
            style=payload.style,
            prompt=payload.prompt,
        )
        return SyntheticHumanRead.model_validate(human)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    except RuntimeError as err:
        logger.exception("create_human_endpoint failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(err),
        ) from err


@router.get("/list", response_model=list[SyntheticHumanRead])
async def list_humans_endpoint(
    user_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[SyntheticHumanRead]:
    """List available synthetic humans, optionally filtered by user."""
    try:
        rows = await list_human_records(db, user_id=user_id)
        return [SyntheticHumanRead.model_validate(row) for row in rows]
    except RuntimeError as err:
        logger.exception("list_humans_endpoint failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(err),
        ) from err


@router.post("/train", response_model=HumanTrainResponse)
async def train_human_endpoint(
    payload: HumanTrainRequest,
    db: Session = Depends(get_db),
) -> HumanTrainResponse:
    """Train synthetic human model from user photos and persist model reference."""
    try:
        human = await train_human_model(db, human_id=payload.human_id, user_photos=payload.user_photos)
        return HumanTrainResponse(
            message="Synthetic human model trained successfully",
            human=SyntheticHumanRead.model_validate(human),
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    except RuntimeError as err:
        logger.exception("train_human_endpoint failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(err),
        ) from err
