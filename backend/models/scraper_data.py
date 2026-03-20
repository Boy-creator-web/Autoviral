"""Scraper data model placeholder."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class ScraperData(Base):
    __tablename__ = "scraper_data"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
