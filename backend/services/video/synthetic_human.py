"""Synthetic Human Generator service."""

from __future__ import annotations

import asyncio
import logging
from uuid import uuid4

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from models.synthetic_human import SyntheticHuman
from models.user import User

logger = logging.getLogger(__name__)


def _style_with_training_tag(style: str, model_ref: str) -> str:
    """Attach a compact training tag and keep value within DB length limit."""
    tag = f"trained:{model_ref[:20]}"
    max_len = 100
    base = style[: max_len - len(tag) - 1]
    return f"{base}|{tag}"


async def create_from_prompt(prompt: str, style: str) -> str:
    """Generate a synthetic human image asset from a prompt.

    Args:
        prompt: Prompt describing facial attributes and overall look.
        style: Visual style preset (for example ``fashion`` or ``lifestyle``).

    Returns:
        Generated image path placeholder.
    """
    try:
        await asyncio.sleep(0)
        image_path = f"/tmp/generated/human_{uuid4().hex}.png"
        logger.info("Created synthetic human from prompt style=%s image=%s", style, image_path)
        logger.debug("Prompt content=%s", prompt)
        return image_path
    except Exception as err:  # pragma: no cover - defensive fallback
        logger.exception("Failed to create synthetic human from prompt")
        raise RuntimeError("Synthetic human generation failed") from err


async def create_from_photo(user_photos: list[str]) -> str:
    """Train a synthetic human model from user photo samples.

    Args:
        user_photos: Collection of image paths or identifiers used for training.

    Returns:
        Trained model reference ID.
    """
    if not user_photos:
        raise ValueError("At least one photo is required for training")

    try:
        await asyncio.sleep(0)
        model_ref = f"human-model-{uuid4().hex}"
        logger.info("Trained synthetic human model_ref=%s samples=%d", model_ref, len(user_photos))
        return model_ref
    except Exception as err:  # pragma: no cover - defensive fallback
        logger.exception("Failed to train synthetic human model")
        raise RuntimeError("Synthetic human model training failed") from err


async def generate_pose(base_human: str, pose_description: str) -> str:
    """Generate an alternate pose image from a base synthetic human.

    Args:
        base_human: Base human identifier or source image path.
        pose_description: Natural language pose instruction.

    Returns:
        Generated posed image path placeholder.
    """
    try:
        await asyncio.sleep(0)
        image_path = f"/tmp/generated/pose_{uuid4().hex}.png"
        logger.info(
            "Generated pose for base_human=%s pose=%s image=%s",
            base_human,
            pose_description,
            image_path,
        )
        return image_path
    except Exception as err:  # pragma: no cover - defensive fallback
        logger.exception("Failed to generate synthetic pose")
        raise RuntimeError("Synthetic human pose generation failed") from err


async def create_human_record(
    db: Session,
    *,
    user_id: int,
    name: str,
    age: int,
    gender: str,
    style: str,
    prompt: str,
) -> SyntheticHuman:
    """Create and persist a synthetic human row after prompt generation."""
    user = db.get(User, user_id)
    if user is None:
        raise ValueError("User not found")

    image_path = await create_from_prompt(prompt, style)
    await generate_pose(image_path, "natural standing pose")

    try:
        human = SyntheticHuman(
            name=name,
            age=age,
            gender=gender,
            style=style,
            user_id=user_id,
        )
        db.add(human)
        db.commit()
        db.refresh(human)
        logger.info("Saved synthetic human id=%s user_id=%s", human.id, user_id)
        return human
    except Exception as err:
        db.rollback()
        logger.exception("Failed to persist synthetic human")
        raise RuntimeError("Failed to persist synthetic human") from err


async def train_human_model(
    db: Session,
    *,
    human_id: int,
    user_photos: list[str],
) -> SyntheticHuman:
    """Train an existing synthetic human and persist model reference in style field."""
    human = db.get(SyntheticHuman, human_id)
    if human is None:
        raise ValueError("Synthetic human not found")

    model_ref = await create_from_photo(user_photos)
    try:
        human.style = _style_with_training_tag(human.style, model_ref)
        db.add(human)
        db.commit()
        db.refresh(human)
        logger.info("Updated synthetic human id=%s with model_ref=%s", human.id, model_ref)
        return human
    except Exception as err:
        db.rollback()
        logger.exception("Failed to update synthetic human model reference")
        raise RuntimeError("Failed to update synthetic human") from err


async def list_human_records(db: Session, *, user_id: int | None = None) -> list[SyntheticHuman]:
    """List synthetic humans with optional user filter."""
    try:
        statement: Select[tuple[SyntheticHuman]] = select(SyntheticHuman).order_by(SyntheticHuman.id)
        if user_id is not None:
            statement = statement.where(SyntheticHuman.user_id == user_id)
        await asyncio.sleep(0)
        return list(db.scalars(statement).all())
    except Exception as err:
        logger.exception("Failed to list synthetic humans")
        raise RuntimeError("Failed to list synthetic humans") from err
