"""
Compatibility endpoint module.

Some code paths import `api.endpoints.human`. Re-export the synthetic human
router to keep those imports working.
"""

from api.endpoints.synthetic_humans import router

__all__ = ["router"]
