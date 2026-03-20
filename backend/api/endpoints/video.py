"""Video endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_video() -> dict[str, str]:
    return {"message": "ok"}


@router.post("/")
def create_video_endpoint() -> dict[str, str]:
    return {"message": "ok"}
