from __future__ import annotations

from typing import Any

import httpx

from core.config import settings


def _post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    url = f"{settings.mirofish_base_url.rstrip('/')}{path}"
    try:
        response = httpx.post(url, json=payload, timeout=settings.mirofish_timeout_seconds)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError:
        # Keep integration resilient if MiroFish is temporarily unavailable.
        return {}


def predict_trends(seed_text: str) -> dict[str, Any]:
    return _post("/api/simulate", {"seed_text": seed_text})


def simulate_audience(product_data: dict[str, Any]) -> dict[str, Any]:
    return _post("/api/simulate", {"product_data": product_data})


def generate_insights() -> dict[str, Any]:
    # Lightweight default call, used by scraper engine when no explicit seed is provided.
    return predict_trends("trend viral indonesia")
