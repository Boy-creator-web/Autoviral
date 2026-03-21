"""Celery tasks for RunPod-backed GPU video rendering."""

from __future__ import annotations

import logging
from typing import Any

from core.celery_app import celery_app
from core.database import SessionLocal
from models.video import Video
from services.runpod.client import (
    RunPodClient,
    render_face_swap,
    render_lip_sync,
    render_video,
)
from services.video.queue import set_job_runpod_mapping

logger = logging.getLogger(__name__)


def _set_video_status(video: Video, *, status: str, file_path: str | None = None) -> None:
    video.status = status
    if file_path is not None:
        video.file_path = file_path


def _extract_output_path(status_payload: dict[str, Any]) -> str | None:
    output = status_payload.get("output")
    if isinstance(output, dict):
        for key in ("video_url", "file_path", "url", "output_url"):
            value = output.get(key)
            if isinstance(value, str) and value:
                return value
    if isinstance(output, str) and output:
        return output
    return None


@celery_app.task(name="runpod.render_video", bind=True)
def runpod_render_video_task(
    self,
    *,
    video_id: int,
    prompt: str,
    human_id: int,
    duration: int,
) -> dict[str, Any]:
    """Submit and monitor RunPod text-to-video job, then update Video row."""
    db = SessionLocal()
    try:
        video = db.get(Video, video_id)
        if video is None:
            raise ValueError(f"Video {video_id} not found")

        _set_video_status(video, status="processing")
        db.add(video)
        db.commit()

        runpod_job_id = render_video(prompt, human_id, duration)
        set_job_runpod_mapping(str(self.request.id), runpod_job_id)

        client = RunPodClient()
        status_payload = client.wait_for_completion(runpod_job_id)
        runpod_status = str(status_payload.get("status", "")).upper()
        if runpod_status != "COMPLETED":
            raise RuntimeError(f"RunPod render_video failed status={runpod_status}")

        output_path = _extract_output_path(status_payload)
        if output_path is None:
            output_path = f"runpod://{runpod_job_id}"

        _set_video_status(video, status="completed", file_path=output_path)
        db.add(video)
        db.commit()
        return {
            "video_id": video_id,
            "status": video.status,
            "file_path": output_path,
            "runpod_job_id": runpod_job_id,
        }
    except Exception:
        db.rollback()
        video = db.get(Video, video_id)
        if video is not None:
            _set_video_status(video, status="failed")
            db.add(video)
            db.commit()
        logger.exception("runpod_render_video_task failed video_id=%s", video_id)
        raise
    finally:
        db.close()


@celery_app.task(name="runpod.render_face_swap", bind=True)
def runpod_render_face_swap_task(
    self,
    *,
    video_id: int,
    source_face: str,
    target_video: str,
) -> dict[str, Any]:
    """Submit and monitor RunPod face-swap job, then update Video row."""
    db = SessionLocal()
    try:
        video = db.get(Video, video_id)
        if video is None:
            raise ValueError(f"Video {video_id} not found")

        _set_video_status(video, status="processing")
        db.add(video)
        db.commit()

        runpod_job_id = render_face_swap(source_face, target_video)
        set_job_runpod_mapping(str(self.request.id), runpod_job_id)

        client = RunPodClient()
        status_payload = client.wait_for_completion(runpod_job_id)
        runpod_status = str(status_payload.get("status", "")).upper()
        if runpod_status != "COMPLETED":
            raise RuntimeError(f"RunPod render_face_swap failed status={runpod_status}")

        output_path = _extract_output_path(status_payload)
        if output_path is None:
            output_path = f"runpod://{runpod_job_id}"

        _set_video_status(video, status="completed", file_path=output_path)
        db.add(video)
        db.commit()
        return {
            "video_id": video_id,
            "status": video.status,
            "file_path": output_path,
            "runpod_job_id": runpod_job_id,
        }
    except Exception:
        db.rollback()
        video = db.get(Video, video_id)
        if video is not None:
            _set_video_status(video, status="failed")
            db.add(video)
            db.commit()
        logger.exception("runpod_render_face_swap_task failed video_id=%s", video_id)
        raise
    finally:
        db.close()


@celery_app.task(name="runpod.render_lip_sync", bind=True)
def runpod_render_lip_sync_task(
    self,
    *,
    video_id: int,
    video_path: str,
    audio_path: str,
) -> dict[str, Any]:
    """Submit and monitor RunPod lip-sync job, then update Video row."""
    db = SessionLocal()
    try:
        video = db.get(Video, video_id)
        if video is None:
            raise ValueError(f"Video {video_id} not found")

        _set_video_status(video, status="processing")
        db.add(video)
        db.commit()

        runpod_job_id = render_lip_sync(video_path, audio_path)
        set_job_runpod_mapping(str(self.request.id), runpod_job_id)

        client = RunPodClient()
        status_payload = client.wait_for_completion(runpod_job_id)
        runpod_status = str(status_payload.get("status", "")).upper()
        if runpod_status != "COMPLETED":
            raise RuntimeError(f"RunPod render_lip_sync failed status={runpod_status}")

        output_path = _extract_output_path(status_payload)
        if output_path is None:
            output_path = f"runpod://{runpod_job_id}"

        _set_video_status(video, status="completed", file_path=output_path)
        db.add(video)
        db.commit()
        return {
            "video_id": video_id,
            "status": video.status,
            "file_path": output_path,
            "runpod_job_id": runpod_job_id,
        }
    except Exception:
        db.rollback()
        video = db.get(Video, video_id)
        if video is not None:
            _set_video_status(video, status="failed")
            db.add(video)
            db.commit()
        logger.exception("runpod_render_lip_sync_task failed video_id=%s", video_id)
        raise
    finally:
        db.close()
