"""Campaign action model for requested user actions."""

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class CampaignAction(Base):
    __tablename__ = "campaign_actions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="queued")

    user = relationship("User", back_populates="actions")
    results = relationship("CampaignResult", back_populates="action", cascade="all, delete-orphan")
