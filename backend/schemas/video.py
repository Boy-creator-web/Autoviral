"""Video schema placeholder."""

from pydantic import BaseModel


class VideoSchema(BaseModel):
    id: int | None = None
    title: str | None = None
