"""Users endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_users() -> dict[str, str]:
    return {"message": "ok"}


@router.post("/")
def create_user() -> dict[str, str]:
    return {"message": "ok"}
