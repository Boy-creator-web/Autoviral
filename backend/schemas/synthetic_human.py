"""Synthetic human schema placeholder."""

from pydantic import BaseModel


class SyntheticHumanSchema(BaseModel):
    id: int | None = None
    name: str | None = None
