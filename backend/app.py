from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.router import api_router
from core.config import settings
from core.database import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.project_name,
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["root"])
def root() -> dict[str, str]:
    return {"message": "Autoviral backend is running"}
