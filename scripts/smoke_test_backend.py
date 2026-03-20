#!/usr/bin/env python3
"""Smoke-test runner for Autoviral backend imports and health endpoints."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any
from urllib import error, request


def _project_paths() -> tuple[Path, Path]:
    root = Path(__file__).resolve().parents[1]
    backend_dir = root / "backend"
    return root, backend_dir


def check_python_imports() -> None:
    """Validate backend can be imported from root and backend contexts."""
    root, backend_dir = _project_paths()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    backend_app = importlib.import_module("backend.app")
    if not hasattr(backend_app, "app"):
        raise RuntimeError("backend.app imported but FastAPI app object not found")

    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    app_module = importlib.import_module("app")
    if not hasattr(app_module, "app"):
        raise RuntimeError("app module imported but FastAPI app object not found")

    print("[OK] Python import checks passed")


def _http_request(url: str, *, method: str = "GET", payload: dict[str, Any] | None = None) -> tuple[int, str]:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = request.Request(url=url, method=method, data=data, headers=headers)
    try:
        with request.urlopen(req, timeout=10) as resp:
            return resp.getcode(), resp.read().decode("utf-8")
    except error.HTTPError as err:
        body = err.read().decode("utf-8")
        return err.code, body


def check_http(base_url: str, *, include_scraper_async: bool = False) -> None:
    """Run lightweight HTTP smoke-tests against a running backend."""
    checks = [
        (f"{base_url}/", {200}),
        (f"{base_url}/api/v1/health", {200}),
        (f"{base_url}/api/v1/health/dependencies", {200, 503}),
    ]

    for url, allowed_codes in checks:
        code, _ = _http_request(url)
        if code not in allowed_codes:
            raise RuntimeError(f"Unexpected status {code} for {url}, expected {sorted(allowed_codes)}")
        print(f"[OK] {url} -> {code}")

    if include_scraper_async:
        payload = {
            "topic": "smoke-test-topic",
            "competitor_signals": ["minor churn"],
            "trend_points": [1.0, 1.1, 1.2],
            "user_actions": ["signup"],
            "comments": ["great product"],
            "competitor_contents": ["basic feature list"],
            "pain_points": ["integration speed"],
            "lead_signals": ["purchase intent"],
        }
        code, body = _http_request(
            f"{base_url}/api/v1/scraper/analyze?run_async=true",
            method="POST",
            payload=payload,
        )
        if code not in {200}:
            raise RuntimeError(f"Unexpected status {code} for scraper async analyze: {body}")
        print("[OK] scraper async analyze endpoint reachable")


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test Autoviral backend")
    parser.add_argument("--url", default="http://localhost:8000", help="Backend base URL")
    parser.add_argument(
        "--skip-http",
        action="store_true",
        help="Only run Python import checks",
    )
    parser.add_argument(
        "--check-scraper-async",
        action="store_true",
        help="Also validate async scraper analyze endpoint",
    )
    args = parser.parse_args()

    try:
        check_python_imports()
        if not args.skip_http:
            check_http(
                args.url.rstrip("/"),
                include_scraper_async=args.check_scraper_async,
            )
        print("[DONE] Smoke-test passed")
        return 0
    except Exception as err:
        print(f"[FAIL] {err}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
