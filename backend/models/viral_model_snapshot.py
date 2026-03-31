from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class ViralModelSnapshot(Base):
    __tablename__ = "viral_model_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    model_type: Mapped[str] = mapped_column(String(80), nullable=False, default="linear_regression_gd")
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mae: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    feature_names_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    weights_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    normalization_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    bias: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
