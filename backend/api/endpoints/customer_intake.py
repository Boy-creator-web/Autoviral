from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from api.schemas import CustomerIntakeCreate, CustomerIntakeListResponse, CustomerIntakeRead
from core.database import get_db
from services.customer_intake_service import create_customer_intake, list_customer_intakes

router = APIRouter()


@router.post("/", response_model=CustomerIntakeRead, status_code=status.HTTP_201_CREATED)
def create_customer_intake_endpoint(
    payload: CustomerIntakeCreate,
    db: Session = Depends(get_db),
) -> CustomerIntakeRead:
    row = create_customer_intake(db, payload)
    return CustomerIntakeRead.model_validate(row)


@router.get("/", response_model=CustomerIntakeListResponse)
def list_customer_intake_endpoint(
    intake_status: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
) -> CustomerIntakeListResponse:
    rows = list_customer_intakes(db, status=intake_status)
    items = [CustomerIntakeRead.model_validate(row) for row in rows]
    return CustomerIntakeListResponse(count=len(items), items=items)
