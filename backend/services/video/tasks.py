"""Celery task definitions for video rendering workflows."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from core.celery_app import celery_app
from core.database import SessionLocal
from models.video import Video
from services.video.audio_engine import sync_lip
from services.video.face_swap import swap_face
from services.video.video_generator import text_to_video

logger = logging.getLogger(__name__)


def _run_async(coro: Any) -> Any:
    return asyncio.run(coro)


def _set_video_status(video: Video, *, status: str, file_path: str | None = None) -> None:
    video.status = status
    if file_path is not None:
        video.file_path = file_path


@celery_app.task(name="video.render_text_video", bind=True)
def render_text_video_task(
    self,
    *,
    video_id: int,
    script: str,
    human_id: int,
    duration: int,
) -> dict[str, Any]:
    """Render a text-driven video and update Video DB state."""
    db = SessionLocal()
    try:
        video = db.get(Video, video_id)
        if video is None:
            raise ValueError(f"Video {video_id} not found")

        _set_video_status(video, status="processing")
        db.add(video)
        db.commit()

        output = _run_async(text_to_video(script, human_id, duration))
        _set_video_status(video, status="completed", file_path=output)
        db.add(video)
        db.commit()
        logger.info("render_text_video completed video_id=%s output=%s", video_id, output)
        return {"video_id": video_id, "status": video.status, "file_path": output}
    except Exception as err:
        db.rollback()
        video = db.get(Video, video_id)
        if video is not None:
            _set_video_status(video, status="failed")
            db.add(video)
            db.commit()
        logger.exception("render_text_video failed video_id=%s", video_id)
        raise err
    finally:
        db.close()


@celery_app.task(name="video.render_face_swap", bind=True)
def render_face_swap_task(
    self,
    *,
    video_id: int,
    source_face: str,
    target_video: str,
) -> dict[str, Any]:
    """Run face-swap rendering and update Video DB state."""
    db = SessionLocal()
    try:
        video = db.get(Video, video_id)
        if video is None:
            raise ValueError(f"Video {video_id} not found")

        _set_video_status(video, status="processing")
        db.add(video)
        db.commit()

        output = _run_async(swap_face(source_face, target_video))
        _set_video_status(video, status="completed", file_path=output)
        db.add(video)
        db.commit()
        logger.info("render_face_swap completed video_id=%s output=%s", video_id, output)
        return {"video_id": video_id, "status": video.status, "file_path": output}
    except Exception as err:
        db.rollback()
        video = db.get(Video, video_id)
        if video is not None:
            _set_video_status(video, status="failed")
            db.add(video)
            db.commit()
        logger.exception("render_face_swap failed video_id=%s", video_id)
        raise err
    finally:
        db.close()


@celery_app.task(name="video.render_lip_sync", bind=True)
def render_lip_sync_task(
    self,
    *,
    video_id: int,
    video_path: str,
    audio_path: str,
) -> dict[str, Any]:
    """Run lip-sync rendering and update Video DB state."""
    db = SessionLocal()
    try:
        video = db.get(Video, video_id)
        if video is None:
            raise ValueError(f"Video {video_id} not found")

        _set_video_status(video, status="processing")
        db.add(video)
        db.commit()

        output = _run_async(sync_lip(video_path, audio_path))
        _set_video_status(video, status="completed", file_path=output)
        db.add(video)
        db.commit()
        logger.info("render_lip_sync completed video_id=%s output=%s", video_id, output)
        return {"video_id": video_id, "status": video.status, "file_path": output}
    except Exception as err:
        db.rollback()
        video = db.get(Video, video_id)
        if video is not None:
            _set_video_status(video, status="failed")
            db.add(video)
            db.commit()
        logger.exception("render_lip_sync failed video_id=%s", video_id)
        raise err
    finally:
        db.close()
