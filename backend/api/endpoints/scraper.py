"""
Compatibility endpoint module.

Some code paths import `api.endpoints.scraper`. Re-export the scraper_data
router to keep those imports working.
"""

from api.endpoints.scraper_data import router

__all__ = ["router"]
