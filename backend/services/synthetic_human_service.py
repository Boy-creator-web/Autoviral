from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from api.schemas import SyntheticHumanCreate
from models.synthetic_human import SyntheticHuman
from models.user import User


def create_synthetic_human(db: Session, payload: SyntheticHumanCreate) -> SyntheticHuman:
    user = db.get(User, payload.user_id)
    if user is None:
        raise ValueError("User not found")

    human = SyntheticHuman(
        name=payload.name,
        age=payload.age,
        gender=payload.gender,
        style=payload.style,
        user_id=payload.user_id,
    )
    db.add(human)
    db.commit()
    db.refresh(human)
    return human


def list_synthetic_humans(db: Session, user_id: int | None = None) -> list[SyntheticHuman]:
    statement: Select[tuple[SyntheticHuman]] = select(SyntheticHuman).order_by(SyntheticHuman.id)
    if user_id is not None:
        statement = statement.where(SyntheticHuman.user_id == user_id)
    return list(db.scalars(statement).all())
