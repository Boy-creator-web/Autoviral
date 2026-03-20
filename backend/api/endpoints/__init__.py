"""API endpoint module exports."""

# Keep explicit absolute imports to ensure `from api.endpoints import human`
# and `from api.endpoints import video` resolve reliably.
from api.endpoints import health
from api.endpoints import human
from api.endpoints import scraper
from api.endpoints import scraper_data
from api.endpoints import synthetic_humans
from api.endpoints import users
from api.endpoints import video
from api.endpoints import videos

__all__ = [
    "human",
    "video",
    "scraper",
    "users",
    "synthetic_humans",
    "videos",
    "health",
    "scraper_data",
]
