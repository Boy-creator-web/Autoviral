from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class ViralVariant(Base):
    __tablename__ = "viral_variants"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    experiment_id: Mapped[int] = mapped_column(
        ForeignKey("viral_experiments.id"),
        nullable=False,
        index=True,
    )
    variant_key: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    hook: Mapped[str] = mapped_column(String(255), nullable=False)
    script: Mapped[str] = mapped_column(Text, nullable=False)
    cta: Mapped[str] = mapped_column(String(255), nullable=False)
    caption: Mapped[str] = mapped_column(String(500), nullable=False)
    hashtags: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    duration_target_sec: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    predicted_hook_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    predicted_watch_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    predicted_share_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    predicted_save_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    predicted_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    experiment = relationship("ViralExperiment", back_populates="variants")
    metrics = relationship(
        "ViralMetric",
        back_populates="variant",
        cascade="all, delete-orphan",
    )
