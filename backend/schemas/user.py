"""User schemas."""

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    full_name: str = Field(min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=50)


class UserRead(BaseModel):
    id: int
    email: str
    full_name: str
    phone: str | None = None
    status: str
