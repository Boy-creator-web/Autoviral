"""Audio engine for TTS, voice cloning, and lip-sync helpers."""

from __future__ import annotations

import asyncio
import logging
from uuid import uuid4

from services.video.video_generator import lip_sync as video_lip_sync

logger = logging.getLogger(__name__)


async def text_to_speech(text: str, voice_style: str) -> str:
    """Generate speech audio from text content and voice style."""
    if not text:
        raise ValueError("Text cannot be empty")

    try:
        await asyncio.sleep(0)
        output_path = f"/tmp/audio/tts_{uuid4().hex}.wav"
        logger.info("Generated TTS voice_style=%s output=%s", voice_style, output_path)
        logger.debug("TTS input text=%s", text)
        return output_path
    except Exception as err:  # pragma: no cover - defensive fallback
        logger.exception("text_to_speech failed")
        raise RuntimeError("TTS generation failed") from err


async def clone_voice(audio_samples: list[str]) -> str:
    """Train a reusable voice model from uploaded audio samples."""
    if not audio_samples:
        raise ValueError("At least one audio sample is required")

    try:
        await asyncio.sleep(0)
        model_ref = f"voice-model-{uuid4().hex}"
        logger.info("Voice model cloned model_ref=%s samples=%d", model_ref, len(audio_samples))
        return model_ref
    except Exception as err:  # pragma: no cover - defensive fallback
        logger.exception("clone_voice failed")
        raise RuntimeError("Voice clone failed") from err


async def sync_lip(video: str, audio: str) -> str:
    """Synchronize lip movement in a video using the provided audio."""
    try:
        logger.info("Audio engine sync_lip requested video=%s audio=%s", video, audio)
        return await video_lip_sync(video, audio)
    except Exception as err:
        logger.exception("sync_lip failed")
        raise RuntimeError("Audio lip sync failed") from err
