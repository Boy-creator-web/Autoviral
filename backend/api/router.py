from fastapi import APIRouter

from api.endpoints import (
    health,
    human,
    scraper,
    scraper_data,
    synthetic_humans,
    users,
    video,
    videos,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(
    synthetic_humans.router,
    prefix="/synthetic-humans",
    tags=["synthetic-humans"],
)
api_router.include_router(videos.router, prefix="/videos", tags=["videos"])
api_router.include_router(scraper_data.router, prefix="/scraper-data", tags=["scraper-data"])
api_router.include_router(scraper.router, prefix="/scraper", tags=["scraper"])
api_router.include_router(video.router, prefix="/video", tags=["video"])
api_router.include_router(human.router, prefix="/human", tags=["human"])
