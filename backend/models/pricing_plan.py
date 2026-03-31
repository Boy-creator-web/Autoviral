"""Pricing plan model."""

from sqlalchemy import Boolean, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class PricingPlan(Base):
    __tablename__ = "pricing_plans"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    price_monthly: Mapped[float] = mapped_column(Float, nullable=False)
    video_quota: Mapped[int] = mapped_column(Integer, nullable=False)
    campaign_quota: Mapped[int] = mapped_column(Integer, nullable=False)
    scraper_quota: Mapped[int] = mapped_column(Integer, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    subscriptions = relationship("Subscription", back_populates="plan", cascade="all, delete-orphan")
