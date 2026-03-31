"""Health endpoint."""

from sqlalchemy import text
from sqlalchemy.orm import Session

from fastapi import APIRouter
from fastapi import Depends, status

from core.database import get_db

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"message": "ok"}


@router.get("/health/db")
def health_db_check(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"message": "ok", "database": "connected", "status": str(status.HTTP_200_OK)}
