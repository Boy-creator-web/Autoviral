"""Scraper endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_scraper() -> dict[str, str]:
    return {"message": "ok"}


@router.post("/")
def run_scraper() -> dict[str, str]:
    return {"message": "ok"}
