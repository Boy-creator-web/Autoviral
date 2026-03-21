"""Orchestration layer for queued video rendering workflows."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from celery.result import AsyncResult
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from core.config import settings
from core.celery_app import celery_app
from models.synthetic_human import SyntheticHuman
from models.user import User
from models.video import Video
from services.runpod.client import RunPodClient
from services.runpod.tasks import (
    runpod_render_face_swap_task,
    runpod_render_lip_sync_task,
    runpod_render_video_task,
)
from services.video.queue import (
    get_job_runpod_mapping,
    get_job_video_mapping,
    register_render_job,
    set_job_video_mapping,
)

logger = logging.getLogger(__name__)


async def _validate_video_owner(db: Session, *, user_id: int, human_id: int) -> None:
    """Validate user and synthetic-human ownership constraints."""
    user = db.get(User, user_id)
    if user is None:
        raise ValueError("User not found")

    human = db.get(SyntheticHuman, human_id)
    if human is None:
        raise ValueError("Synthetic human not found")
    if human.user_id != user_id:
        raise ValueError("Synthetic human does not belong to the selected user")
    await asyncio.sleep(0)


async def _create_queued_video(
    db: Session,
    *,
    title: str,
    user_id: int,
    human_id: int,
) -> Video:
    """Create a queued Video row before Celery execution."""
    try:
        video = Video(
            title=title,
            status="queued",
            file_path=None,
            human_id=human_id,
            user_id=user_id,
        )
        db.add(video)
        db.commit()
        db.refresh(video)
        await asyncio.sleep(0)
        return video
    except Exception as err:
        db.rollback()
        logger.exception("Failed to create queued video row")
        raise RuntimeError("Failed to create video job record") from err


async def queue_text_video_job(
    db: Session,
    *,
    title: str,
    script: str,
    human_id: int,
    user_id: int,
    duration: int,
) -> tuple[str, Video]:
    """Queue script-to-video rendering in Celery and return job metadata."""
    try:
        await _validate_video_owner(db, user_id=user_id, human_id=human_id)
        video = await _create_queued_video(db, title=title, user_id=user_id, human_id=human_id)
        task = runpod_render_video_task.apply_async(
            kwargs={
                "video_id": video.id,
                "prompt": script,
                "human_id": human_id,
                "duration": duration,
            },
            queue=settings.video_queue_name,
        )
        register_render_job(task.id, {"operation": "generate", "video_id": video.id})
        set_job_video_mapping(task.id, video.id)
        logger.info("Queued text video task id=%s video_id=%s", task.id, video.id)
        return task.id, video
    except ValueError:
        raise
    except Exception as err:
        logger.exception("Failed to queue text video job")
        raise RuntimeError("Failed to queue text video job") from err


async def queue_face_swap_job(
    db: Session,
    *,
    title: str,
    source_face: str,
    target_video: str,
    user_id: int,
    human_id: int,
) -> tuple[str, Video]:
    """Queue face swap rendering task."""
    try:
        await _validate_video_owner(db, user_id=user_id, human_id=human_id)
        video = await _create_queued_video(db, title=title, user_id=user_id, human_id=human_id)
        task = runpod_render_face_swap_task.apply_async(
            kwargs={
                "video_id": video.id,
                "source_face": source_face,
                "target_video": target_video,
            },
            queue=settings.video_queue_name,
        )
        register_render_job(task.id, {"operation": "swap_face", "video_id": video.id})
        set_job_video_mapping(task.id, video.id)
        logger.info("Queued face swap task id=%s video_id=%s", task.id, video.id)
        return task.id, video
    except ValueError:
        raise
    except Exception as err:
        logger.exception("Failed to queue face swap job")
        raise RuntimeError("Failed to queue face swap job") from err


async def queue_lip_sync_job(
    db: Session,
    *,
    title: str,
    video_path: str,
    audio_path: str,
    user_id: int,
    human_id: int,
) -> tuple[str, Video]:
    """Queue lip-sync rendering task."""
    try:
        await _validate_video_owner(db, user_id=user_id, human_id=human_id)
        video = await _create_queued_video(db, title=title, user_id=user_id, human_id=human_id)
        task = runpod_render_lip_sync_task.apply_async(
            kwargs={
                "video_id": video.id,
                "video_path": video_path,
                "audio_path": audio_path,
            },
            queue=settings.video_queue_name,
        )
        register_render_job(task.id, {"operation": "lip_sync", "video_id": video.id})
        set_job_video_mapping(task.id, video.id)
        logger.info("Queued lip-sync task id=%s video_id=%s", task.id, video.id)
        return task.id, video
    except ValueError:
        raise
    except Exception as err:
        logger.exception("Failed to queue lip-sync job")
        raise RuntimeError("Failed to queue lip-sync job") from err


async def get_render_job_status(db: Session, *, job_id: str) -> dict[str, Any]:
    """Resolve Celery + database status for a rendering job ID."""
    try:
        result = AsyncResult(job_id, app=celery_app)
        video_id = get_job_video_mapping(job_id)
        runpod_job_id = get_job_runpod_mapping(job_id)
        runpod_status: str | None = None
        video_status: str | None = None
        file_path: str | None = None

        if video_id is not None:
            statement: Select[tuple[Video]] = select(Video).where(Video.id == video_id)
            video = db.scalar(statement)
            if video is not None:
                video_status = video.status
                file_path = video.file_path

        if runpod_job_id:
            try:
                runpod_payload = RunPodClient().get_status(runpod_job_id)
                runpod_status = str(runpod_payload.get("status")) if runpod_payload else None
            except Exception:
                logger.exception("Failed to resolve RunPod status job_id=%s", job_id)

        await asyncio.sleep(0)
        return {
            "job_id": job_id,
            "state": result.state,
            "video_id": video_id,
            "video_status": video_status,
            "file_path": file_path,
            "runpod_job_id": runpod_job_id,
            "runpod_status": runpod_status,
            "result": result.result if result.successful() else None,
            "error": str(result.result) if result.failed() else None,
        }
    except Exception as err:
        logger.exception("Failed to fetch render job status job_id=%s", job_id)
        raise RuntimeError("Failed to fetch render job status") from err
