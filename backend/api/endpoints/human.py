"""Human endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_humans() -> dict[str, str]:
    return {"message": "ok"}


@router.post("/")
def create_human() -> dict[str, str]:
    return {"message": "ok"}
