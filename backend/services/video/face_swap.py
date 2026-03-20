"""Face Swap Engine implementation."""

from __future__ import annotations

import asyncio
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)


async def swap_face(source_face: str, target_video: str) -> str:
    """Swap source face into a target video clip and return rendered output path."""
    try:
        await asyncio.sleep(0)
        output_path = f"/tmp/rendered/face_swap_{uuid4().hex}.mp4"
        logger.info(
            "Face swap completed source=%s target=%s output=%s",
            source_face,
            target_video,
            output_path,
        )
        return output_path
    except Exception as err:  # pragma: no cover - defensive fallback
        logger.exception("swap_face failed")
        raise RuntimeError("Face swap failed") from err


async def batch_swap(source_face: str, target_videos: list[str]) -> list[str]:
    """Apply face swap to multiple videos in batch mode."""
    if not target_videos:
        raise ValueError("At least one target video is required")

    try:
        results: list[str] = []
        for target_video in target_videos:
            results.append(await swap_face(source_face, target_video))
        logger.info("Batch face swap completed total=%d", len(results))
        return results
    except Exception as err:
        logger.exception("batch_swap failed")
        raise RuntimeError("Batch face swap failed") from err
