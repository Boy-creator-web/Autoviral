from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from core.config import settings


class PosterError(RuntimeError):
    pass


def _base_url() -> str:
    return settings.postiz_api_base_url.rstrip("/")


def _headers() -> dict[str, str]:
    if not settings.postiz_api_key:
        raise PosterError("POSTIZ_API_KEY is not configured")
    return {"Authorization": settings.postiz_api_key}


def _normalize_platform(platform: str) -> str:
    normalized = platform.strip().lower()
    if normalized == "twitter":
        return "x"
    return normalized


def _integration_id_for_platform(platform: str) -> str:
    normalized = _normalize_platform(platform)
    try:
        mapping = json.loads(settings.postiz_integration_ids_json)
    except json.JSONDecodeError as err:
        raise PosterError("POSTIZ_INTEGRATION_IDS_JSON is invalid JSON") from err

    integration_id = str(mapping.get(normalized, "")).strip()
    if not integration_id:
        raise PosterError(f"Integration ID for platform '{normalized}' is not configured")
    return integration_id


def _settings_for_platform(platform: str, tags: list[str]) -> dict[str, Any]:
    platform_lower = _normalize_platform(platform)
    if platform_lower == "x":
        return {"__type": "x", "who_can_reply_post": "everyone"}
    if platform_lower == "instagram":
        return {"__type": "instagram", "post_type": "post"}
    if platform_lower == "youtube":
        return {
            "__type": "youtube",
            "title": "Autoviral Upload",
            "type": "public",
            "selfDeclaredMadeForKids": False,
            "tags": tags,
        }
    if platform_lower == "facebook":
        return {"__type": "facebook"}
    if platform_lower == "linkedin":
        return {"__type": "linkedin"}
    if platform_lower == "tiktok":
        return {
            "__type": "tiktok",
            "privacy_level": "PUBLIC_TO_EVERYONE",
            "duet": False,
            "stitch": False,
            "comment": True,
            "autoAddMusic": True,
            "brand_content_toggle": False,
            "brand_organic_toggle": True,
            "content_posting_method": "DIRECT_POST",
        }
    raise PosterError(f"Unsupported platform: {platform}")


def _upload_file(video_path: str) -> dict[str, Any]:
    path = Path(video_path)
    if not path.exists():
        raise PosterError(f"Video file not found: {video_path}")

    try:
        with path.open("rb") as file_handle:
            response = httpx.post(
                f"{_base_url()}/upload",
                headers=_headers(),
                files={"file": (path.name, file_handle, "video/mp4")},
                timeout=settings.postiz_timeout_seconds,
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as err:
        raise PosterError("Failed to upload media to Postiz") from err


def _create_post_payload(
    *,
    integration_id: str,
    platform: str,
    caption: str,
    tags: list[str],
    upload_file: dict[str, Any],
    post_type: str,
    scheduled_at: datetime | None = None,
) -> dict[str, Any]:
    date_value = scheduled_at or datetime.now(UTC)
    return {
        "type": post_type,
        "date": date_value.isoformat(),
        "shortLink": False,
        "tags": tags,
        "posts": [
            {
                "integration": {"id": integration_id},
                "value": [
                    {
                        "content": caption,
                        "image": [
                            {
                                "id": upload_file.get("id"),
                                "path": upload_file.get("path"),
                            }
                        ],
                    }
                ],
                "settings": _settings_for_platform(platform, tags),
            }
        ],
    }


def _create_post(payload: dict[str, Any]) -> str:
    try:
        response = httpx.post(
            f"{_base_url()}/posts",
            headers={**_headers(), "Content-Type": "application/json"},
            json=payload,
            timeout=settings.postiz_timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        post_id = str(data.get("id", "")).strip()
        if not post_id:
            raise PosterError("Postiz did not return post id")
        return post_id
    except httpx.HTTPError as err:
        raise PosterError("Failed to create post on Postiz") from err


def _coerce_schedule_time(schedule_time: datetime | str) -> datetime:
    if isinstance(schedule_time, datetime):
        return schedule_time
    iso_text = schedule_time.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(iso_text)
    except ValueError as err:
        raise PosterError("schedule_time must be ISO-8601 datetime") from err


def post_to_social(platform: str, video_path: str, caption: str, tags: list[str]) -> str:
    upload_file = _upload_file(video_path)
    payload = _create_post_payload(
        integration_id=_integration_id_for_platform(platform),
        platform=platform,
        caption=caption,
        tags=tags,
        upload_file=upload_file,
        post_type="now",
    )
    return _create_post(payload)


def schedule_post(
    platform: str,
    video_path: str,
    caption: str,
    tags: list[str],
    schedule_time: datetime | str,
) -> str:
    upload_file = _upload_file(video_path)
    payload = _create_post_payload(
        integration_id=_integration_id_for_platform(platform),
        platform=platform,
        caption=caption,
        tags=tags,
        upload_file=upload_file,
        post_type="schedule",
        scheduled_at=_coerce_schedule_time(schedule_time),
    )
    return _create_post(payload)


def get_post_status(post_id: str) -> dict[str, Any]:
    try:
        response = httpx.get(
            f"{_base_url()}/posts",
            headers=_headers(),
            timeout=settings.postiz_timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as err:
        raise PosterError("Failed to fetch post status from Postiz") from err

    rows: list[dict[str, Any]]
    if isinstance(data, list):
        rows = data
    elif isinstance(data, dict) and isinstance(data.get("items"), list):
        rows = data["items"]
    else:
        rows = []

    for row in rows:
        if str(row.get("id")) == str(post_id):
            return row
    return {"id": post_id, "status": "unknown"}
