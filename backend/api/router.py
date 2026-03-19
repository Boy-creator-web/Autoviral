from fastapi import APIRouter

from api.endpoints import health, scraper_data, synthetic_humans, users, videos

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
