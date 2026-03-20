"""Automated smoke-test for Autoviral API endpoints.

This test suite expects the backend service (and its dependencies) to be
running, typically via docker compose.
"""

from __future__ import annotations

import os
import time
import uuid
from typing import Any

import pytest
import requests

BASE_URL = os.getenv("AUTOVIRAL_BASE_URL", "http://localhost:8000").rstrip("/")
API_PREFIX = os.getenv("AUTOVIRAL_API_PREFIX", "/api/v1").rstrip("/")
REQUEST_TIMEOUT = float(os.getenv("AUTOVIRAL_SMOKE_TIMEOUT", "15"))
STATUS_POLL_ATTEMPTS = int(os.getenv("AUTOVIRAL_STATUS_POLL_ATTEMPTS", "10"))
STATUS_POLL_INTERVAL = float(os.getenv("AUTOVIRAL_STATUS_POLL_INTERVAL", "1.5"))


def _endpoint(path: str) -> str:
    return f"{BASE_URL}{API_PREFIX}{path}"


def _assert_schema(payload: dict[str, Any], required_fields: dict[str, type]) -> None:
    """Validate required field existence and types in JSON payload."""
    for field, expected_type in required_fields.items():
        assert field in payload, f"Missing response field '{field}' in payload={payload}"
        assert isinstance(
            payload[field],
            expected_type,
        ), f"Field '{field}' expected {expected_type}, got {type(payload[field])}: {payload}"


def _request_json(
    method: str,
    path: str,
    *,
    expected_statuses: tuple[int, ...] = (200, 201),
    json_payload: dict[str, Any] | None = None,
) -> dict[str, Any] | list[dict[str, Any]]:
    """Send request and return parsed JSON with rich failure diagnostics."""
    try:
        response = requests.request(
            method=method,
            url=_endpoint(path),
            json=json_payload,
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as err:
        pytest.fail(f"Request failed for {method} {path}: {err}")

    if response.status_code not in expected_statuses:
        pytest.fail(
            f"Unexpected status for {method} {path}. "
            f"expected={expected_statuses}, got={response.status_code}, body={response.text}"
        )

    try:
        return response.json()
    except ValueError as err:
        pytest.fail(
            f"Response is not valid JSON for {method} {path}. "
            f"status={response.status_code}, body={response.text}, error={err}"
        )


def _create_user() -> dict[str, Any]:
    unique = uuid.uuid4().hex[:8]
    payload = {
        "email": f"smoke_{unique}@example.com",
        "password": "SmokeTest123!",
        "name": f"Smoke User {unique}",
    }
    response = _request_json("POST", "/users", expected_statuses=(201,), json_payload=payload)
    assert isinstance(response, dict)
    _assert_schema(
        response,
        {
            "id": int,
            "email": str,
            "name": str,
            "created_at": str,
        },
    )
    return response


def test_smoke_autoviral_endpoints() -> None:
    """Smoke-test key endpoints after backend fixes."""
    health_payload = _request_json("GET", "/health", expected_statuses=(200,))
    assert isinstance(health_payload, dict)
    _assert_schema(health_payload, {"status": str})
    assert health_payload["status"] == "ok"

    user = _create_user()

    create_human_payload = {
        "name": "Smoke Human",
        "age": 28,
        "gender": "female",
        "style": "fashion",
        "user_id": user["id"],
    }
    created_human = _request_json(
        "POST",
        "/synthetic-humans/",
        expected_statuses=(201,),
        json_payload=create_human_payload,
    )
    assert isinstance(created_human, dict)
    _assert_schema(
        created_human,
        {
            "id": int,
            "name": str,
            "age": int,
            "gender": str,
            "style": str,
            "user_id": int,
        },
    )
    assert created_human["user_id"] == user["id"]

    listed_humans = _request_json(
        "GET",
        f"/synthetic-humans/?user_id={user['id']}",
        expected_statuses=(200,),
    )
    assert isinstance(listed_humans, list), f"Expected list, got {type(listed_humans)}"
    assert any(
        isinstance(item, dict) and item.get("id") == created_human["id"]
        for item in listed_humans
    ), f"Newly created synthetic human id={created_human['id']} not found in list"

    scraper_payload = {
        "topic": "smoke-test-topic",
        "competitor_signals": ["minor churn in competitor support"],
        "trend_points": [1.0, 1.1, 1.25],
        "user_actions": ["signup", "pricing_view"],
        "comments": ["great product", "easy to use"],
        "competitor_contents": ["basic analytics only"],
        "pain_points": ["automation workflow"],
        "lead_signals": ["purchase", "budget approved"],
    }
    scraper_job = _request_json(
        "POST",
        "/scraper/analyze?run_async=true",
        expected_statuses=(200, 201),
        json_payload=scraper_payload,
    )
    assert isinstance(scraper_job, dict)
    _assert_schema(scraper_job, {"job_id": str, "status": str, "results": list})
    job_id = scraper_job["job_id"]

    latest_status: dict[str, Any] | None = None
    for _ in range(STATUS_POLL_ATTEMPTS):
        status_payload = _request_json(
            "GET",
            f"/scraper/status/{job_id}",
            expected_statuses=(200,),
        )
        assert isinstance(status_payload, dict)
        _assert_schema(status_payload, {"job_id": str, "state": str})
        assert status_payload["job_id"] == job_id
        latest_status = status_payload
        if status_payload["state"] in {"SUCCESS", "FAILURE"}:
            break
        time.sleep(STATUS_POLL_INTERVAL)

    assert latest_status is not None, "Failed to retrieve scraper job status"

    video_payload = {
        "user_id": user["id"],
        "human_id": created_human["id"],
        "title": "Smoke Video Generate",
        "script": "This is a smoke test video script.",
        "duration": 12,
    }
    video_job = _request_json(
        "POST",
        "/video/generate",
        expected_statuses=(200, 201),
        json_payload=video_payload,
    )
    assert isinstance(video_job, dict)
    _assert_schema(video_job, {"job_id": str, "video": dict, "status": str})
    _assert_schema(
        video_job["video"],
        {
            "id": int,
            "title": str,
            "status": str,
            "human_id": int,
            "user_id": int,
        },
    )
