"""Main API router."""

from fastapi import APIRouter

from api.endpoints.health import router as health_router
from api.endpoints.human import router as human_router
from api.endpoints.scraper import router as scraper_router
from api.endpoints.synthetic_humans import router as synthetic_humans_router
from api.endpoints.users import router as users_router
from api.endpoints.video import router as video_router
from api.endpoints.videos import router as videos_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(
    synthetic_humans_router,
    prefix="/synthetic-humans",
    tags=["synthetic-humans"],
)
api_router.include_router(videos_router, prefix="/videos", tags=["videos"])
api_router.include_router(scraper_router, prefix="/scraper", tags=["scraper"])
api_router.include_router(video_router, prefix="/video", tags=["video"])
api_router.include_router(human_router, prefix="/human", tags=["human"])
