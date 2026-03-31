"""Video schemas."""

from pydantic import BaseModel, Field


class VideoCreate(BaseModel):
    user_id: int
    synthetic_human_id: int | None = None
    title: str = Field(min_length=1, max_length=255)
    status: str = Field(default="draft", min_length=1, max_length=50)
    url: str | None = Field(default=None, max_length=500)


class VideoRead(BaseModel):
    id: int
    user_id: int
    synthetic_human_id: int | None = None
    title: str
    status: str
    url: str | None = None
