from __future__ import annotations

from typing import Any

import httpx

from core.config import settings


def _base_url() -> str:
    return settings.mirofish_base_url.rstrip("/")


def _safe_get(path: str) -> dict[str, Any]:
    try:
        response = httpx.get(f"{_base_url()}{path}", timeout=settings.mirofish_timeout_seconds)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError:
        return {}


def _safe_post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        response = httpx.post(
            f"{_base_url()}{path}",
            json=payload,
            timeout=settings.mirofish_timeout_seconds,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError:
        return {}


def _project_list_summary() -> dict[str, Any]:
    """
    Fallback for newer MiroFish deployments where `/api/simulate` does not exist.
    """
    project_list = _safe_get("/api/graph/project/list")
    projects = []
    if isinstance(project_list, dict):
        data = project_list.get("data")
        if isinstance(data, list):
            projects = data
    return {
        "source": "mirofish-project-list",
        "project_count": len(projects),
        "projects": projects[:5],
    }


def predict_trends(seed_text: str) -> dict[str, Any]:
    legacy = _safe_post("/api/simulate", {"seed_text": seed_text})
    if legacy:
        return legacy
    fallback = _project_list_summary()
    fallback["seed_text"] = seed_text
    return fallback


def simulate_audience(product_data: dict[str, Any]) -> dict[str, Any]:
    legacy = _safe_post("/api/simulate", {"product_data": product_data})
    if legacy:
        return legacy
    fallback = _project_list_summary()
    fallback["product_data"] = product_data
    return fallback


def generate_insights() -> dict[str, Any]:
    health = _safe_get("/health")
    trends = predict_trends("trend viral indonesia")
    return {
        "health": health,
        "trends_snapshot": trends,
    }
