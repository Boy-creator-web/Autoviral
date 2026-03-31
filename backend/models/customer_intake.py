from datetime import datetime

from sqlalchemy import DateTime, Float, String, Text, func
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

