"""Scraper schemas."""

from pydantic import BaseModel, Field


class ScraperDataCreate(BaseModel):
    user_id: int
    topic: str = Field(min_length=1, max_length=255)
    source: str = Field(default="manual", min_length=1, max_length=100)
    insight: str = Field(min_length=1)


class ScraperDataRead(BaseModel):
    id: int
    user_id: int
    topic: str
    source: str
    insight: str
    status: str
