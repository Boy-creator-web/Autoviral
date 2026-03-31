"""Synthetic human schemas."""

from pydantic import BaseModel, Field


class SyntheticHumanCreate(BaseModel):
    user_id: int
    name: str = Field(min_length=1, max_length=255)
    style: str = Field(default="default", min_length=1, max_length=100)


class SyntheticHumanRead(BaseModel):
    id: int
    user_id: int
    name: str
    style: str


class SyntheticHumanSchema(BaseModel):
    id: int | None = None
    name: str | None = None
