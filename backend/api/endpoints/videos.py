from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.schemas import VideoCreate, VideoRead
from core.database import get_db
from services.video_service import create_video, list_videos

router = APIRouter()


@router.post("/", response_model=VideoRead, status_code=status.HTTP_201_CREATED)
def create_video_endpoint(payload: VideoCreate, db: Session = Depends(get_db)) -> VideoRead:
    try:
        video = create_video(db, payload)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return VideoRead.model_validate(video)


@router.get("/", response_model=list[VideoRead])
def list_videos_endpoint(
    user_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[VideoRead]:
    videos = list_videos(db, user_id=user_id)
    return [VideoRead.model_validate(video) for video in videos]
