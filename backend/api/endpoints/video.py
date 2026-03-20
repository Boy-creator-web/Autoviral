"""
Compatibility endpoint module.

Some code paths import `api.endpoints.video`. Re-export the videos
router to keep those imports working.
"""

from api.endpoints.videos import router

__all__ = ["router"]
