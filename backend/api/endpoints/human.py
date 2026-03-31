"""Alias endpoint to synthetic humans for compatibility."""

from api.endpoints.synthetic_humans import create_synthetic_human, list_synthetic_humans
from api.endpoints.synthetic_humans import router as router

__all__ = [
    "router",
    "list_synthetic_humans",
    "create_synthetic_human",
]
