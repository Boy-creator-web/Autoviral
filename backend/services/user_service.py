from sqlalchemy import select
from sqlalchemy.orm import Session

from api.schemas import UserCreate
from core.security import get_password_hash
from models.user import User


def create_user(db: Session, payload: UserCreate) -> User:
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise ValueError("Email already registered")

    user = User(
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        name=payload.name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id)).all())
