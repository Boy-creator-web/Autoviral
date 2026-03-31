"""Campaign result model."""

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class CampaignResult(Base):
    __tablename__ = "campaign_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    action_id: Mapped[int] = mapped_column(ForeignKey("campaign_actions.id"), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(String(255), nullable=False)
    result_data: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="completed")

    action = relationship("CampaignAction", back_populates="results")
