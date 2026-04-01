from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.schemas import (
    CustomerEngineStartRequest,
    CustomerEngineStartResponse,
    CustomerIntakeCreate,
    CustomerIntakeListResponse,
    CustomerIntakeRead,
    CustomerPaymentConfirmRequest,
)
from core.database import get_db
from services.customer_intake_service import (
    confirm_customer_payment,
    create_customer_intake,
    list_customer_intakes,
    start_engine_for_intake,
)

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


@router.post("/confirm-payment", response_model=CustomerIntakeRead)
def confirm_payment_endpoint(
    payload: CustomerPaymentConfirmRequest,
    db: Session = Depends(get_db),
) -> CustomerIntakeRead:
    try:
        row = confirm_customer_payment(
            db=db,
            intake_id=payload.intake_id,
            payment_reference=payload.payment_reference,
            payment_method=payload.payment_method,
            payment_amount=payload.payment_amount,
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return CustomerIntakeRead.model_validate(row)


@router.post("/start-engine", response_model=CustomerEngineStartResponse)
def start_engine_endpoint(
    payload: CustomerEngineStartRequest,
    db: Session = Depends(get_db),
) -> CustomerEngineStartResponse:
    try:
        intake, run, plan = start_engine_for_intake(
            db=db,
            intake_id=payload.intake_id,
            started_by=payload.started_by,
            interval_minutes=payload.interval_minutes,
            plan_name=payload.plan_name,
            run_now=payload.run_now,
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return CustomerEngineStartResponse(
        intake=CustomerIntakeRead.model_validate(intake),
        run={
            "id": run.id,
            "status": run.status,
            "experiment_id": run.experiment_id,
            "selected_variant_id": run.selected_variant_id,
            "discovered_leads_count": run.discovered_leads_count,
            "qualified_leads_count": run.qualified_leads_count,
            "drafted_outreach_count": run.drafted_outreach_count,
        }
        if run
        else None,
        plan={
            "id": plan.id,
            "name": plan.name,
            "interval_minutes": plan.interval_minutes,
            "is_active": plan.is_active,
            "next_run_at": plan.next_run_at.isoformat() if plan.next_run_at else None,
            "last_run_at": plan.last_run_at.isoformat() if plan.last_run_at else None,
            "last_status": plan.last_status,
        },
    )
