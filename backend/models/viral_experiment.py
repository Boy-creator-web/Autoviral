from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class ViralExperiment(Base):
    __tablename__ = "viral_experiments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    video_id: Mapped[int | None] = mapped_column(ForeignKey("videos.id"), nullable=True, index=True)
    niche: Mapped[str] = mapped_column(String(150), nullable=False)
    audience: Mapped[str] = mapped_column(String(200), nullable=False)
    objective: Mapped[str] = mapped_column(String(200), nullable=False)
    problem_angle: Mapped[str] = mapped_column(String(255), nullable=False)
    offer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tone: Mapped[str] = mapped_column(String(80), nullable=False, default="direct")
    platform: Mapped[str] = mapped_column(String(50), nullable=False, default="tiktok")
    trend_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="running", index=True)
    baseline_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    variants = relationship(
        "ViralVariant",
        back_populates="experiment",
        cascade="all, delete-orphan",
    )
