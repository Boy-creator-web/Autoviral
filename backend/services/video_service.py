from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from api.schemas import VideoCreate
from models.synthetic_human import SyntheticHuman
from models.user import User
from models.video import Video
from services.poster import (
    PosterError,
    get_post_status,
    post_to_social,
    schedule_post,
)


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

    # Auto-post workflow: when render is complete and a file exists, trigger Postiz.
    if (
        payload.auto_publish_platforms
        and video.status == "completed"
        and video.file_path
    ):
        try:
            post_ids: list[str] = []
            for platform in payload.auto_publish_platforms:
                post_id = post_to_social(
                    platform=platform,
                    video_path=video.file_path,
                    caption=payload.caption or video.title,
                    tags=payload.tags or ["autoviral"],
                )
                post_ids.append(post_id)
            video.status = f"posted:{','.join(post_ids)}"
            db.commit()
            db.refresh(video)
        except PosterError:
            # Keep primary transaction successful; status indicates posting issue.
            video.status = "post_failed"
            db.commit()
            db.refresh(video)

    return video


def list_videos(db: Session, user_id: int | None = None) -> list[Video]:
    statement: Select[tuple[Video]] = select(Video).order_by(Video.id)
    if user_id is not None:
        statement = statement.where(Video.user_id == user_id)
    return list(db.scalars(statement).all())


def trigger_video_distribution(
    db: Session,
    video_id: int,
    platform: str,
    caption: str,
    tags: list[str] | None = None,
    schedule_time: str | None = None,
) -> dict:
    video = db.get(Video, video_id)
    if video is None:
        raise ValueError("Video not found")
    if not video.file_path:
        raise ValueError("Video file_path is required for distribution")

    if schedule_time:
        post_id = schedule_post(
            platform=platform,
            video_path=video.file_path,
            caption=caption,
            tags=tags or [],
            schedule_time=schedule_time,
        )
    else:
        post_id = post_to_social(
            platform=platform,
            video_path=video.file_path,
            caption=caption,
            tags=tags or [],
        )

    status = get_post_status(post_id)
    video.status = f"posted:{post_id}"
    db.commit()
    db.refresh(video)
    return {"post_id": post_id, "post_status": status, "video_id": video.id}
