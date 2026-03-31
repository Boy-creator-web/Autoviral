"""Payment model."""

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    subscription_id: Mapped[int | None] = mapped_column(ForeignKey("subscriptions.id"), nullable=True, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="IDR")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    provider: Mapped[str] = mapped_column(String(100), nullable=False, default="manual")
    invoice_no: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)

    user = relationship("User", back_populates="payments")
    subscription = relationship("Subscription", back_populates="payments")
