"""Synthetic humans endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_synthetic_humans() -> dict[str, str]:
    return {"message": "ok"}


@router.post("/")
def create_synthetic_human() -> dict[str, str]:
    return {"message": "ok"}
