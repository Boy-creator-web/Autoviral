"""Users endpoint for registration and listing."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException, status

from core.database import get_db
from models.user import User
from schemas.user import UserCreate, UserRead

router = APIRouter()


@router.get("/", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)) -> list[UserRead]:
    rows = list(db.scalars(select(User).order_by(User.id.desc())).all())
    return [
        UserRead(
            id=row.id,
            email=row.email,
            full_name=row.full_name,
            phone=row.phone,
            status=row.status,
        )
        for row in rows
    ]


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        phone=payload.phone,
        status="active",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        status=user.status,
    )
