"""Video model placeholder."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
