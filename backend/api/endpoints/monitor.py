"""Operational monitor endpoints for production checks."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from core.security import get_admin_user

router = APIRouter()


def _backup_status() -> dict[str, Any]:
    backup_dir = Path(settings.backup_dir)
    latest_file = None
    latest_time = None

    if backup_dir.exists():
        candidates = sorted(backup_dir.glob("autoviral_*.sql.gz"), key=lambda p: p.stat().st_mtime, reverse=True)
        if candidates:
            latest_file = candidates[0]
            latest_time = datetime.fromtimestamp(latest_file.stat().st_mtime, tz=timezone.utc)

    now = datetime.now(timezone.utc)
    stale_threshold = timedelta(minutes=settings.backup_stale_minutes)
    stale = True
    age_minutes = None
    if latest_time is not None:
        delta = now - latest_time
        age_minutes = int(delta.total_seconds() // 60)
        stale = delta > stale_threshold

    next_expected = now + timedelta(seconds=settings.monitor_interval_seconds)
    return {
        "backup_dir": str(backup_dir),
        "latest_backup_file": str(latest_file) if latest_file else None,
        "latest_backup_utc": latest_time.isoformat() if latest_time else None,
        "latest_backup_age_minutes": age_minutes,
        "stale": stale,
        "next_check_utc": next_expected.isoformat(),
    }


@router.get("/status", dependencies=[Depends(get_admin_user)])
def monitor_status(db: Session = Depends(get_db)) -> dict[str, Any]:
    now = datetime.now(timezone.utc)

    db_ok = False
    db_error = None
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as err:  # pragma: no cover - defensive
        db_error = str(err)

    redis_ok = False
    redis_error = None
    try:
        redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
        redis_client.ping()
        redis_ok = True
    except RedisError as err:
        redis_error = str(err)

    backup = _backup_status()
    overall_ok = db_ok and redis_ok and (not backup["stale"]) 

    return {
        "message": "ok" if overall_ok else "degraded",
        "checked_at": now.isoformat(),
        "services": {
            "database": {"ok": db_ok, "error": db_error},
            "redis": {"ok": redis_ok, "error": redis_error},
        },
        "backup": backup,
    }
