"""Autoviral backend entrypoint."""

from fastapi import FastAPI

from api.router import api_router
from core.config import settings

app = FastAPI(title=settings.project_name, version="1.0.0")
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["root"])
def root() -> dict[str, str]:
    return {"message": "ok"}
