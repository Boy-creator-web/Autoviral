from __future__ import annotations

import asyncio
import contextlib

from core.config import settings
from core.database import SessionLocal
from services.autonomous_orchestrator_service import run_due_autonomous_plans

_scheduler_task: asyncio.Task | None = None
_stop_event: asyncio.Event | None = None


async def _scheduler_loop() -> None:
    assert _stop_event is not None
    while not _stop_event.is_set():
        db = SessionLocal()
        try:
            run_due_autonomous_plans(db)
        finally:
            db.close()
        try:
            await asyncio.wait_for(_stop_event.wait(), timeout=max(1, settings.autonomous_scheduler_tick_seconds))
        except asyncio.TimeoutError:
            continue


def start_scheduler() -> None:
    global _scheduler_task, _stop_event
    if _scheduler_task is not None:
        return
    if not settings.autonomous_scheduler_enabled:
        return
    _stop_event = asyncio.Event()
    _scheduler_task = asyncio.create_task(_scheduler_loop())


async def stop_scheduler() -> None:
    global _scheduler_task, _stop_event
    if _scheduler_task is None:
        return
    assert _stop_event is not None
    _stop_event.set()
    _scheduler_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await _scheduler_task
    _scheduler_task = None
    _stop_event = None
