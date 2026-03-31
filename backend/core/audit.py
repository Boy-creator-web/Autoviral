"""Audit logging helper for critical actions."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("autoviral.audit")


def audit_log(event: str, *, actor: str, target: str, metadata: dict[str, Any] | None = None) -> None:
    """Write structured audit event to application logs."""
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "actor": actor,
        "target": target,
        "metadata": metadata or {},
    }
    logger.info("AUDIT %s", json.dumps(payload, ensure_ascii=True))
