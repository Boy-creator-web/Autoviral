"""Video Factory API endpoints."""

from __future__ import annotations

import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.schemas import (
    VideoGenerateRequest,
    VideoJobQueuedResponse,
    VideoJobStatusResponse,
    VideoLipSyncRequest,
    VideoRead,
    VideoSwapFaceRequest,
)
from core.database import get_db
from models.synthetic_human import SyntheticHuman
from models.user import User
from models.video import Video
from services.video.manager import (
    get_render_job_status,
    queue_face_swap_job,
    queue_lip_sync_job,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/generate", response_model=VideoJobQueuedResponse, status_code=status.HTTP_201_CREATED)
async def generate_video_endpoint(
    payload: VideoGenerateRequest,
    db: Session = Depends(get_db),
) -> VideoJobQueuedResponse:
    """Return dummy video generation response without real rendering."""
    try:
        user = db.get(User, payload.user_id)
        if user is None:
            raise ValueError("User not found")

        human = db.get(SyntheticHuman, payload.human_id)
        if human is None:
            raise ValueError("Synthetic human not found")
        if human.user_id != payload.user_id:
            raise ValueError("Synthetic human does not belong to the selected user")

        video = Video(
            title=payload.title,
            status="mock_completed",
            file_path=f"/mock/videos/{payload.human_id}_{uuid4().hex}.mp4",
            human_id=payload.human_id,
            user_id=payload.user_id,
        )
        db.add(video)
        db.commit()
        db.refresh(video)

        return VideoJobQueuedResponse(
            job_id=f"mock-{uuid4().hex}",
            video=VideoRead.model_validate(video),
            status="mock_completed",
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    except RuntimeError as err:
        logger.exception("generate_video_endpoint failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(err),
        ) from err


@router.post("/swap-face", response_model=VideoJobQueuedResponse, status_code=status.HTTP_202_ACCEPTED)
async def swap_face_endpoint(
    payload: VideoSwapFaceRequest,
    db: Session = Depends(get_db),
) -> VideoJobQueuedResponse:
    """Queue a face swap rendering job."""
    try:
        job_id, video = await queue_face_swap_job(
            db,
            title=payload.title,
            source_face=payload.source_face,
            target_video=payload.target_video,
            user_id=payload.user_id,
            human_id=payload.human_id,
        )
        return VideoJobQueuedResponse(
            job_id=job_id,
            video=VideoRead.model_validate(video),
            status="queued",
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    except RuntimeError as err:
        logger.exception("swap_face_endpoint failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(err),
        ) from err


@router.post("/lip-sync", response_model=VideoJobQueuedResponse, status_code=status.HTTP_202_ACCEPTED)
async def lip_sync_endpoint(
    payload: VideoLipSyncRequest,
    db: Session = Depends(get_db),
) -> VideoJobQueuedResponse:
    """Queue a lip-sync rendering job."""
    try:
        job_id, video = await queue_lip_sync_job(
            db,
            title=payload.title,
            video_path=payload.video_path,
            audio_path=payload.audio_path,
            user_id=payload.user_id,
            human_id=payload.human_id,
        )
        return VideoJobQueuedResponse(
            job_id=job_id,
            video=VideoRead.model_validate(video),
            status="queued",
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    except RuntimeError as err:
        logger.exception("lip_sync_endpoint failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(err),
        ) from err


@router.get("/status/{job_id}", response_model=VideoJobStatusResponse)
async def render_status_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
) -> VideoJobStatusResponse:
    """Fetch render status from Celery and persisted Video row."""
    try:
        status_payload = await get_render_job_status(db, job_id=job_id)
        return VideoJobStatusResponse.model_validate(status_payload)
    except RuntimeError as err:
        logger.exception("render_status_endpoint failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(err),
        ) from err
