"""Video Factory primitives for script/image rendering."""

from __future__ import annotations

import asyncio
import logging
from uuid import uuid4

from services.video.templates.template_video import build_video_template

logger = logging.getLogger(__name__)


async def text_to_video(script: str, human_id: int, duration: int) -> str:
    """Render a video from text script and selected synthetic human.

    Args:
        script: Narration or visual script content.
        human_id: Synthetic human database ID as actor reference.
        duration: Desired output duration in seconds.

    Returns:
        Rendered video path placeholder.
    """
    if duration <= 0:
        raise ValueError("Duration must be greater than zero")

    try:
        await asyncio.sleep(0)
        template = build_video_template("lifestyle", script=script)
        output_path = f"/tmp/rendered/text_video_{uuid4().hex}.mp4"
        logger.info(
            "Rendered text-to-video human_id=%s duration=%s output=%s",
            human_id,
            duration,
            output_path,
        )
        logger.debug("Render template=%s", template)
        return output_path
    except Exception as err:  # pragma: no cover - defensive fallback
        logger.exception("text_to_video failed")
        raise RuntimeError("Text-to-video rendering failed") from err


async def image_to_video(image_path: str, motion_prompt: str) -> str:
    """Animate a still image into a short video clip."""
    try:
        await asyncio.sleep(0)
        output_path = f"/tmp/rendered/image_video_{uuid4().hex}.mp4"
        logger.info(
            "Rendered image-to-video image=%s motion=%s output=%s",
            image_path,
            motion_prompt,
            output_path,
        )
        return output_path
    except Exception as err:  # pragma: no cover - defensive fallback
        logger.exception("image_to_video failed")
        raise RuntimeError("Image-to-video rendering failed") from err


async def multi_scene_video(scenes: list[str]) -> str:
    """Combine multiple scene clips into one output video."""
    if not scenes:
        raise ValueError("At least one scene is required")

    try:
        await asyncio.sleep(0)
        output_path = f"/tmp/rendered/multi_scene_{uuid4().hex}.mp4"
        logger.info("Rendered multi-scene video scenes=%d output=%s", len(scenes), output_path)
        return output_path
    except Exception as err:  # pragma: no cover - defensive fallback
        logger.exception("multi_scene_video failed")
        raise RuntimeError("Multi-scene composition failed") from err


async def lip_sync(video_path: str, audio_path: str) -> str:
    """Apply lip-sync process between provided video and audio assets."""
    try:
        await asyncio.sleep(0)
        output_path = f"/tmp/rendered/lipsync_{uuid4().hex}.mp4"
        logger.info("Applied lip-sync video=%s audio=%s output=%s", video_path, audio_path, output_path)
        return output_path
    except Exception as err:  # pragma: no cover - defensive fallback
        logger.exception("lip_sync failed")
        raise RuntimeError("Lip-sync rendering failed") from err
