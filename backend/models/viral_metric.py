from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class ViralMetric(Base):
    __tablename__ = "viral_metrics"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    variant_id: Mapped[int] = mapped_column(
        ForeignKey("viral_variants.id"),
        nullable=False,
        index=True,
    )
    impressions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    views_3s: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    views_10s: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    likes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    comments: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    shares: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    saves: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    profile_visits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    link_clicks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    watch_time_avg_sec: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    conversion_events: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    variant = relationship("ViralVariant", back_populates="metrics")
