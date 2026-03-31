from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class AutonomousRun(Base):
    __tablename__ = "autonomous_runs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    video_id: Mapped[int | None] = mapped_column(ForeignKey("videos.id"), nullable=True, index=True)
    seed_text: Mapped[str] = mapped_column(String(500), nullable=False)
    niche: Mapped[str] = mapped_column(String(150), nullable=False)
    audience: Mapped[str] = mapped_column(String(200), nullable=False)
    objective: Mapped[str] = mapped_column(String(200), nullable=False)
    region: Mapped[str] = mapped_column(String(100), nullable=False, default="ID")
    platform: Mapped[str] = mapped_column(String(50), nullable=False, default="tiktok")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="completed", index=True)
    insight_topic: Mapped[str | None] = mapped_column(String(255), nullable=True)
    experiment_id: Mapped[int | None] = mapped_column(ForeignKey("viral_experiments.id"), nullable=True, index=True)
    selected_variant_id: Mapped[int | None] = mapped_column(ForeignKey("viral_variants.id"), nullable=True, index=True)
    discovered_leads_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    qualified_leads_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    drafted_outreach_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    summary_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
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
