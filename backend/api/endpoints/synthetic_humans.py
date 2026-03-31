"""Synthetic humans endpoint."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException, status

from core.database import get_db
from models.synthetic_human import SyntheticHuman
from models.user import User
from schemas.synthetic_human import SyntheticHumanCreate, SyntheticHumanRead

router = APIRouter()


@router.get("/", response_model=list[SyntheticHumanRead])
def list_synthetic_humans(db: Session = Depends(get_db)) -> list[SyntheticHumanRead]:
    rows = list(db.scalars(select(SyntheticHuman).order_by(SyntheticHuman.id.desc())).all())
    return [
        SyntheticHumanRead(
            id=row.id,
            user_id=row.user_id,
            name=row.name,
            style=row.style,
        )
        for row in rows
    ]


@router.post("/", response_model=SyntheticHumanRead, status_code=status.HTTP_201_CREATED)
def create_synthetic_human(payload: SyntheticHumanCreate, db: Session = Depends(get_db)) -> SyntheticHumanRead:
    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    row = SyntheticHuman(user_id=payload.user_id, name=payload.name, style=payload.style)
    db.add(row)
    db.commit()
    db.refresh(row)
    return SyntheticHumanRead(id=row.id, user_id=row.user_id, name=row.name, style=row.style)
