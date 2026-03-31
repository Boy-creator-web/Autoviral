"""Database setup and initialization."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create database tables for all registered models."""
    from models import (  # noqa: F401
        audit_log,
        campaign_action,
        campaign_report,
        campaign_result,
        payment,
        pricing_plan,
        scraper_data,
        subscription,
        synthetic_human,
        user,
        video,
    )

    Base.metadata.create_all(bind=engine)
