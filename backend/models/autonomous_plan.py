from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class AutonomousPlan(Base):
    __tablename__ = "autonomous_plans"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    video_id: Mapped[int | None] = mapped_column(ForeignKey("videos.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    seed_text: Mapped[str] = mapped_column(String(500), nullable=False)
    niche: Mapped[str] = mapped_column(String(150), nullable=False)
    audience: Mapped[str] = mapped_column(String(200), nullable=False)
    objective: Mapped[str] = mapped_column(String(200), nullable=False)
    problem_angle: Mapped[str] = mapped_column(String(255), nullable=False)
    offer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tone: Mapped[str] = mapped_column(String(80), nullable=False, default="direct")
    platform: Mapped[str] = mapped_column(String(50), nullable=False, default="tiktok")
    region: Mapped[str] = mapped_column(String(100), nullable=False, default="ID")
    leads_count: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    variants_count: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=360)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
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
