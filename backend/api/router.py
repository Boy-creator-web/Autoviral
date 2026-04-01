"""Main API router."""

from fastapi import APIRouter

from api.endpoints.actions import router as actions_router
from api.endpoints.auth import router as auth_router
from api.endpoints.customer_intake import router as customer_intake_router
from api.endpoints.health import router as health_router
from api.endpoints.human import router as human_router
from api.endpoints.monitor import router as monitor_router
from api.endpoints.operations import router as operations_router
from api.endpoints.payments import router as payments_router
from api.endpoints.pricing import router as pricing_router
from api.endpoints.reports import router as reports_router
from api.endpoints.results import router as results_router
from api.endpoints.scraper import router as scraper_router
from api.endpoints.subscriptions import router as subscriptions_router
from api.endpoints.synthetic_humans import router as synthetic_humans_router
from api.endpoints.users import router as users_router
from api.endpoints.video import router as video_router
from api.endpoints.videos import router as videos_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(customer_intake_router, prefix="/customer-intake", tags=["customer-intake"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
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
api_router.include_router(pricing_router, prefix="/pricing", tags=["pricing"])
api_router.include_router(subscriptions_router, prefix="/subscriptions", tags=["subscriptions"])
api_router.include_router(payments_router, prefix="/payments", tags=["payments"])
api_router.include_router(actions_router, prefix="/actions", tags=["actions"])
api_router.include_router(results_router, prefix="/results", tags=["results"])
api_router.include_router(reports_router, prefix="/reports", tags=["reports"])
api_router.include_router(operations_router, prefix="/operations", tags=["operations"])
api_router.include_router(monitor_router, prefix="/monitor", tags=["monitor"])
