from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from api.schemas import VideoCreate
from models.synthetic_human import SyntheticHuman
from models.user import User
from models.video import Video


def create_video(db: Session, payload: VideoCreate) -> Video:
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
        status=payload.status,
        file_path=payload.file_path,
        human_id=payload.human_id,
        user_id=payload.user_id,
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    return video


def list_videos(db: Session, user_id: int | None = None) -> list[Video]:
    statement: Select[tuple[Video]] = select(Video).order_by(Video.id)
    if user_id is not None:
        statement = statement.where(Video.user_id == user_id)
    return list(db.scalars(statement).all())
