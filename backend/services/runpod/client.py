"""RunPod API client helpers for video rendering workflows."""

from __future__ import annotations

import logging
from typing import Any

import requests

from core.config import settings

logger = logging.getLogger(__name__)

RUNPOD_API_BASE = "https://api.runpod.ai/v2"


class RunPodClient:
    """Minimal RunPod API client for submit/status operations."""

    def __init__(self, *, api_key: str | None = None, endpoint_id: str | None = None) -> None:
        self.api_key = api_key or settings.runpod_api_key
        self.endpoint_id = endpoint_id or settings.runpod_endpoint_id
        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def submit(self, payload: dict[str, Any]) -> str:
        """Submit a rendering payload to RunPod and return runpod job id."""
        url = f"{RUNPOD_API_BASE}/{self.endpoint_id}/run"
        response = requests.post(url, headers=self._headers, json={"input": payload}, timeout=45)
        response.raise_for_status()
        body = response.json()
        runpod_job_id = body.get("id")
        if not runpod_job_id:
            raise RuntimeError(f"RunPod submit response missing id: {body}")
        logger.info("Submitted RunPod job endpoint=%s runpod_job_id=%s", self.endpoint_id, runpod_job_id)
        return str(runpod_job_id)

    def get_status(self, runpod_job_id: str) -> dict[str, Any]:
        """Fetch RunPod job status payload."""
        url = f"{RUNPOD_API_BASE}/{self.endpoint_id}/status/{runpod_job_id}"
        response = requests.get(url, headers=self._headers, timeout=30)
        response.raise_for_status()
        return response.json()

    def wait_for_completion(
        self,
        runpod_job_id: str,
        *,
        max_polls: int = 120,
        poll_interval_sec: float = 3.0,
    ) -> dict[str, Any]:
        """Poll RunPod status until completion or failure."""
        import time

        last_payload: dict[str, Any] = {}
        for _ in range(max_polls):
            status_payload = self.get_status(runpod_job_id)
            last_payload = status_payload
            status_value = str(status_payload.get("status", "")).upper()
            if status_value in {"COMPLETED", "FAILED", "CANCELLED"}:
                return status_payload
            time.sleep(poll_interval_sec)
        raise TimeoutError(
            f"RunPod job timeout runpod_job_id={runpod_job_id} last_status={last_payload.get('status')}"
        )


def render_video(prompt: str, human_id: int, duration: int) -> str:
    """Submit text-to-video rendering job to RunPod and return job id."""
    client = RunPodClient()
    return client.submit(
        {
            "operation": "render_video",
            "prompt": prompt,
            "human_id": human_id,
            "duration": duration,
        }
    )


def render_face_swap(source_face: str, target_video: str) -> str:
    """Submit face-swap rendering job to RunPod and return job id."""
    client = RunPodClient()
    return client.submit(
        {
            "operation": "render_face_swap",
            "source_face": source_face,
            "target_video": target_video,
        }
    )


def render_lip_sync(video_path: str, audio_path: str) -> str:
    """Submit lip-sync rendering job to RunPod and return job id."""
    client = RunPodClient()
    return client.submit(
        {
            "operation": "render_lip_sync",
            "video_path": video_path,
            "audio_path": audio_path,
        }
    )
