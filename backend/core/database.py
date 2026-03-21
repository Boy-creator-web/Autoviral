import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()

# Database URL dari environment variable
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@postgres:5432/autoviral",
)

# Create engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# SessionLocal untuk dependency injection
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class untuk models
Base = declarative_base()


def get_db() -> Session:
    """Dependency untuk mendapatkan database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database (create tables)"""
    from models import scraper_data, synthetic_human, user, video

    Base.metadata.create_all(bind=engine)
