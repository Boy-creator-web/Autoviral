from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.schemas import (
    HumanCompatCreateRequest,
    HumanCompatListResponse,
    HumanCompatRead,
    HumanCompatTrainRequest,
    HumanCompatTrainResponse,
)
from core.database import get_db
from services.human_compat_service import (
    create_human_compat,
    list_human_compat,
    train_human_voice_compat,
)

router = APIRouter()


@router.post("/create", response_model=HumanCompatRead, status_code=status.HTTP_201_CREATED)
def human_create_endpoint(
    payload: HumanCompatCreateRequest,
    db: Session = Depends(get_db),
) -> HumanCompatRead:
    try:
        row = create_human_compat(
            db=db,
            name=payload.name,
            age=payload.age,
            gender=payload.gender,
            style=payload.style,
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return HumanCompatRead(
        id=row.id,
        name=row.name,
        age=row.age,
        gender=row.gender,
        style=row.style,
        user_id=row.user_id,
    )


@router.get("/list", response_model=HumanCompatListResponse)
def human_list_endpoint(db: Session = Depends(get_db)) -> HumanCompatListResponse:
    rows = list_human_compat(db=db)
    items = [
        HumanCompatRead(
            id=row.id,
            name=row.name,
            age=row.age,
            gender=row.gender,
            style=row.style,
            user_id=row.user_id,
        )
        for row in rows
    ]
    return HumanCompatListResponse(count=len(items), items=items)


@router.post("/train", response_model=HumanCompatTrainResponse)
def human_train_endpoint(
    payload: HumanCompatTrainRequest,
    db: Session = Depends(get_db),
) -> HumanCompatTrainResponse:
    try:
        _, audio_file = train_human_voice_compat(
            db=db,
            human_id=payload.human_id,
            text=payload.text,
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return HumanCompatTrainResponse(ok=True, human_id=payload.human_id, audio_file=audio_file)
