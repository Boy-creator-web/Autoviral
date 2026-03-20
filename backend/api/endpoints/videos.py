"""Videos endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_videos() -> dict[str, str]:
    return {"message": "ok"}


@router.post("/")
def create_video() -> dict[str, str]:
    return {"message": "ok"}
