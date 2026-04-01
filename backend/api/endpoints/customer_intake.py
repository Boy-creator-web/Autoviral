from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.schemas import (
    CustomerAiCsChatRequest,
    CustomerAiCsChatResponse,
    CustomerCheckoutCreateRequest,
    CustomerCheckoutCreateResponse,
    CustomerSocialCredentialRead,
    CustomerEngineStartRequest,
    CustomerEngineStartResponse,
    CustomerIntakeCreate,
    CustomerIntakeListResponse,
    CustomerIntakeRead,
    CustomerPaymentConfirmRequest,
)
from core.database import get_db
from services.customer_intake_service import (
    apply_midtrans_notification,
    confirm_customer_payment,
    create_customer_intake,
    generate_ai_cs_reply,
    get_customer_intake,
    list_checkout_social_credentials,
    list_customer_intakes,
    save_checkout_social_credentials,
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


@router.post("/midtrans/webhook")
def midtrans_webhook_endpoint(
    payload: dict,
    db: Session = Depends(get_db),
) -> dict:
    try:
        row = apply_midtrans_notification(db=db, payload=payload)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return {
        "ok": True,
        "updated": row is not None,
        "intake_id": row.id if row else None,
        "payment_status": row.payment_status if row else None,
    }


@router.post("/checkout", response_model=CustomerCheckoutCreateResponse)
def create_checkout_with_social_accounts_endpoint(
    payload: CustomerCheckoutCreateRequest,
    db: Session = Depends(get_db),
) -> CustomerCheckoutCreateResponse:
    try:
        intake, rows = save_checkout_social_credentials(
            db=db,
            intake_id=payload.intake_id,
            payment_method=payload.payment_method,
            preferred_plan=payload.preferred_plan,
            social_accounts=payload.social_accounts,
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return CustomerCheckoutCreateResponse(
        intake=CustomerIntakeRead.model_validate(intake),
        social_accounts_count=len(rows),
        social_accounts=[CustomerSocialCredentialRead.model_validate(item) for item in rows],
    )


@router.get("/checkout/{intake_id}", response_model=CustomerCheckoutCreateResponse)
def get_checkout_social_accounts_endpoint(
    intake_id: int,
    db: Session = Depends(get_db),
) -> CustomerCheckoutCreateResponse:
    try:
        intake = get_customer_intake(db=db, intake_id=intake_id)
        rows = list_checkout_social_credentials(db=db, intake_id=intake_id)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    return CustomerCheckoutCreateResponse(
        intake=CustomerIntakeRead.model_validate(intake),
        social_accounts_count=len(rows),
        social_accounts=[CustomerSocialCredentialRead.model_validate(item) for item in rows],
    )


@router.post("/ai-cs/chat", response_model=CustomerAiCsChatResponse)
def ai_cs_chat_endpoint(payload: CustomerAiCsChatRequest) -> CustomerAiCsChatResponse:
    reply, suggested_actions, suggested_plan, handoff_required = generate_ai_cs_reply(
        message=payload.message,
        customer_name=payload.customer_name,
        business_name=payload.business_name,
    )
    return CustomerAiCsChatResponse(
        reply=reply,
        suggested_actions=suggested_actions,
        suggested_plan=suggested_plan,
        handoff_required=handoff_required,
    )


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
