from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class CustomerIntake(Base):
    __tablename__ = "customer_intakes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    business_name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    niche: Mapped[str] = mapped_column(String(150), nullable=False)
    product_name: Mapped[str] = mapped_column(String(180), nullable=False)
    product_category: Mapped[str] = mapped_column(String(120), nullable=False)
    product_price_range: Mapped[str] = mapped_column(String(120), nullable=False)
    business_model: Mapped[str] = mapped_column(String(80), nullable=False)
    target_customer_profile: Mapped[str] = mapped_column(Text, nullable=False)
    target_region: Mapped[str] = mapped_column(String(120), nullable=False)
    main_platforms: Mapped[str] = mapped_column(String(255), nullable=False)
    primary_kpi: Mapped[str] = mapped_column(String(120), nullable=False)
    current_monthly_leads: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_conversion_rate_percent: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sales_cycle_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    monthly_marketing_budget: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    preferred_contact_time: Mapped[str] = mapped_column(String(120), nullable=False)
    monthly_revenue_target: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    preferred_plan: Mapped[str] = mapped_column(String(50), nullable=False, default="starter")
    pain_point: Mapped[str] = mapped_column(Text, nullable=False)
    desired_outcome: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(120), nullable=False, default="website")
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="new", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

