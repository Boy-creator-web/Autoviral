from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.schemas import SyntheticHumanCreate, SyntheticHumanRead
from core.database import get_db
from services.synthetic_human_service import create_synthetic_human, list_synthetic_humans

router = APIRouter()


@router.post("/", response_model=SyntheticHumanRead, status_code=status.HTTP_201_CREATED)
def create_synthetic_human_endpoint(
    payload: SyntheticHumanCreate, db: Session = Depends(get_db)
) -> SyntheticHumanRead:
    try:
        human = create_synthetic_human(db, payload)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return SyntheticHumanRead.model_validate(human)


@router.get("/", response_model=list[SyntheticHumanRead])
def list_synthetic_humans_endpoint(
    user_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[SyntheticHumanRead]:
    humans = list_synthetic_humans(db, user_id=user_id)
    return [SyntheticHumanRead.model_validate(human) for human in humans]
