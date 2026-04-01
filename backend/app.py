from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from api.router import api_router
from core.config import settings
from core.database import init_db
from services.autonomous_scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    start_scheduler()
    yield
    await stop_scheduler()


app = FastAPI(
    title=settings.project_name,
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=f"{settings.api_v1_prefix}/openapi.json" if settings.docs_enabled else None,
)

app.include_router(api_router, prefix=settings.api_v1_prefix)

if settings.allowed_hosts_csv.strip():
    allowed_hosts = [item.strip() for item in settings.allowed_hosts_csv.split(",") if item.strip()]
    if allowed_hosts:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)


@app.middleware("http")
async def api_key_protection(request: Request, call_next):
    if not settings.api_key_required:
        return await call_next(request)

    path = request.url.path
    allowlist = {
        "/",
        f"{settings.api_v1_prefix}/health",
    }
    if path in allowlist:
        return await call_next(request)

    # Public website lead form must remain accessible for first-touch customer intake.
    if request.method.upper() == "POST" and path in {
        f"{settings.api_v1_prefix}/customer-intake",
        f"{settings.api_v1_prefix}/customer-intake/",
        f"{settings.api_v1_prefix}/customer-intake/checkout",
        f"{settings.api_v1_prefix}/customer-intake/checkout/",
        f"{settings.api_v1_prefix}/customer-intake/midtrans/webhook",
        f"{settings.api_v1_prefix}/customer-intake/midtrans/webhook/",
        f"{settings.api_v1_prefix}/customer-intake/ai-cs/chat",
        f"{settings.api_v1_prefix}/customer-intake/ai-cs/chat/",
    }:
        return await call_next(request)

    if settings.docs_enabled and path in {
        "/docs",
        "/redoc",
        f"{settings.api_v1_prefix}/openapi.json",
    }:
        return await call_next(request)

    expected = settings.api_key.strip()
    provided = request.headers.get("X-API-Key", "").strip()
    if not expected:
        return JSONResponse(status_code=503, content={"detail": "API key is not configured"})
    if provided != expected:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    return await call_next(request)


@app.get("/", tags=["root"])
def root() -> dict[str, str]:
    return {"message": "Autoviral backend is running"}


if settings.docs_enabled:
    @app.get("/docs", include_in_schema=False)
    def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=f"{settings.api_v1_prefix}/openapi.json",
            title=f"{settings.project_name} - Swagger UI",
        )


    @app.get("/redoc", include_in_schema=False)
    def redoc_html():
        return get_redoc_html(
            openapi_url=f"{settings.api_v1_prefix}/openapi.json",
            title=f"{settings.project_name} - ReDoc",
        )
