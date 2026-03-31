"""Audit logging helper for critical actions."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("autoviral.audit")


def audit_log(
    event: str,
    *,
    actor: str,
    target: str,
    metadata: dict[str, Any] | None = None,
    db: object | None = None,
) -> None:
    """Write structured audit event to logs and DB (best effort)."""
    # Lazy imports prevent circular import during module initialization.
    from core.database import SessionLocal
    from models.audit_log import AuditLog

    payload_metadata = dict(metadata or {})
    user_id: int | None = None
    actor_user_id = payload_metadata.get("actor_user_id")
    if isinstance(actor_user_id, int):
        user_id = actor_user_id
    elif actor.startswith("user:"):
        candidate = actor.split(":", 1)[1].strip()
        if candidate.isdigit():
            user_id = int(candidate)
    elif actor.isdigit():
        user_id = int(actor)
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "actor": actor,
        "target": target,
        "metadata": payload_metadata,
    }
    logger.info("AUDIT %s", json.dumps(payload, ensure_ascii=True))

    # Never fail business request because of audit persistence problems.
    try:
        with SessionLocal() as session:
            row = AuditLog(
                user_id=user_id,
                event=event,
                actor=actor,
                target=target,
                metadata_json=json.dumps(payload_metadata, ensure_ascii=True),
            )
            session.add(row)
            session.commit()
    except Exception:  # pragma: no cover - defensive
        logger.exception(
            "Audit persistence failed",
            extra={"event": event, "actor": actor, "target": target},
        )
