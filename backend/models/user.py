from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    synthetic_humans = relationship(
        "SyntheticHuman",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    videos = relationship("Video", back_populates="user", cascade="all, delete-orphan")
