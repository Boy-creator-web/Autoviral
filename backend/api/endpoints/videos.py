"""Videos endpoint."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException, status

from core.database import get_db
from core.security import get_current_user
from models.synthetic_human import SyntheticHuman
from models.user import User
from models.video import Video
from schemas.video import VideoCreate, VideoRead

router = APIRouter()


@router.get("/", response_model=list[VideoRead])
def list_videos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[VideoRead]:
    rows = list(db.scalars(select(Video).order_by(Video.id.desc())).all())
    if current_user.role != "admin":
        rows = [row for row in rows if row.user_id == current_user.id]
    return [
        VideoRead(
            id=row.id,
            user_id=row.user_id,
            title=row.title,
            status=row.status,
            url=row.url,
            synthetic_human_id=row.synthetic_human_id,
        )
        for row in rows
    ]


@router.post("/", response_model=VideoRead, status_code=status.HTTP_201_CREATED)
def create_video(
    payload: VideoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VideoRead:
    if current_user.role != "admin" and current_user.id != payload.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed for this user")

    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if payload.synthetic_human_id is not None:
        human = db.get(SyntheticHuman, payload.synthetic_human_id)
        if human is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Synthetic human not found")

    row = Video(
        user_id=payload.user_id,
        title=payload.title,
        status=payload.status,
        url=payload.url,
        synthetic_human_id=payload.synthetic_human_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return VideoRead(
        id=row.id,
        user_id=row.user_id,
        title=row.title,
        status=row.status,
        url=row.url,
        synthetic_human_id=row.synthetic_human_id,
    )
