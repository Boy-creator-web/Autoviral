"""Scraper data schema placeholder."""

from pydantic import BaseModel


class ScraperDataSchema(BaseModel):
    id: int | None = None
    topic: str | None = None
