from sqlalchemy import Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class ScraperData(Base):
    __tablename__ = "scraper_data"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    intent_score: Mapped[float] = mapped_column(Float, nullable=False)
    raw_data: Mapped[str] = mapped_column(Text, nullable=False)
