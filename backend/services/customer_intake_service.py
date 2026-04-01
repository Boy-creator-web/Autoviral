import hashlib

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from api.schemas import CustomerIntakeCreate
from core.config import settings
from models.customer_intake import CustomerIntake
from models.user import User
from services.autonomous_orchestrator_service import bootstrap_daily_mode
from services.user_service import create_user


class _UserPayload:
    def __init__(self, *, email: str, password: str, name: str) -> None:
        self.email = email
        self.password = password
        self.name = name


def _safe_username_from_full_name(full_name: str) -> str:
    tokens = [part for part in full_name.strip().split() if part]
    if not tokens:
        return "Client"
    return " ".join(tokens[:2])[:255]


def _derive_objective_from_kpi(primary_kpi: str) -> str:
    mapping = {
        "qualified_leads": "increase qualified leads",
        "sales_conversion": "increase sales conversion",
        "revenue_growth": "increase revenue growth",
        "cac_efficiency": "improve CAC efficiency",
    }
    key = (primary_kpi or "").strip().lower()
    return mapping.get(key, "increase sales leads")


def create_customer_intake(db: Session, payload: CustomerIntakeCreate) -> CustomerIntake:
    row = CustomerIntake(
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        business_name=payload.business_name,
        niche=payload.niche,
        product_name=payload.product_name,
        product_category=payload.product_category,
        product_price_range=payload.product_price_range,
        business_model=payload.business_model,
        target_customer_profile=payload.target_customer_profile,
        target_region=payload.target_region,
        main_platforms=payload.main_platforms,
        primary_kpi=payload.primary_kpi,
        current_monthly_leads=payload.current_monthly_leads,
        current_conversion_rate_percent=payload.current_conversion_rate_percent,
        sales_cycle_days=payload.sales_cycle_days,
        monthly_marketing_budget=payload.monthly_marketing_budget,
        preferred_contact_time=payload.preferred_contact_time,
        monthly_revenue_target=payload.monthly_revenue_target,
        preferred_plan=payload.preferred_plan,
        pain_point=payload.pain_point,
        desired_outcome=payload.desired_outcome,
        source=payload.source,
        status="new",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_customer_intakes(db: Session, status: str | None = None) -> list[CustomerIntake]:
    statement: Select[tuple[CustomerIntake]] = select(CustomerIntake).order_by(CustomerIntake.id.desc())
    if status:
        statement = statement.where(CustomerIntake.status == status)
    return list(db.scalars(statement).all())


def get_customer_intake(db: Session, *, intake_id: int) -> CustomerIntake:
    row = db.get(CustomerIntake, intake_id)
    if row is None:
        raise ValueError("Customer intake not found")
    return row


def confirm_customer_payment(
    db: Session,
    *,
    intake_id: int,
    payment_reference: str,
    payment_method: str,
    payment_amount: float,
) -> CustomerIntake:
    row = get_customer_intake(db, intake_id=intake_id)
    row.mark_payment_received(
        reference=payment_reference,
        method=payment_method,
        amount=payment_amount,
    )
    row.status = "payment_confirmed"
    db.commit()
    db.refresh(row)
    return row


def _extract_intake_id_from_order_id(order_id: str) -> int:
    value = order_id.strip()
    prefix = "INTAKE-"
    if not value.upper().startswith(prefix):
        raise ValueError("Unsupported order_id format")
    try:
        return int(value[len(prefix):])
    except ValueError as err:
        raise ValueError("Invalid intake ID in order_id") from err


def verify_midtrans_signature(
    *,
    order_id: str,
    status_code: str,
    gross_amount: str,
    signature_key: str,
) -> bool:
    server_key = settings.midtrans_server_key.strip()
    if not server_key:
        return False
    raw = f"{order_id}{status_code}{gross_amount}{server_key}"
    computed = hashlib.sha512(raw.encode("utf-8")).hexdigest()
    return computed == signature_key


def apply_midtrans_notification(db: Session, payload: dict) -> CustomerIntake | None:
    order_id = str(payload.get("order_id") or "").strip()
    transaction_status = str(payload.get("transaction_status") or "").strip().lower()
    fraud_status = str(payload.get("fraud_status") or "").strip().lower()
    status_code = str(payload.get("status_code") or "")
    gross_amount = str(payload.get("gross_amount") or "")
    signature_key = str(payload.get("signature_key") or "")
    payment_type = str(payload.get("payment_type") or "midtrans")

    if not order_id or not status_code or not gross_amount or not signature_key:
        raise ValueError("Incomplete Midtrans notification payload")
    if not verify_midtrans_signature(
        order_id=order_id,
        status_code=status_code,
        gross_amount=gross_amount,
        signature_key=signature_key,
    ):
        raise ValueError("Invalid Midtrans signature")

    intake_id = _extract_intake_id_from_order_id(order_id)
    intake = get_customer_intake(db, intake_id=intake_id)

    success = transaction_status in {"settlement", "capture"} and (
        transaction_status == "settlement" or fraud_status in {"", "accept"}
    )
    if not success:
        return None

    intake.mark_payment_received(
        reference=order_id,
        method=payment_type or "midtrans",
        amount=float(gross_amount or 0),
    )
    intake.status = "payment_confirmed"
    db.commit()
    db.refresh(intake)
    return intake


def _user_for_intake(db: Session, intake: CustomerIntake):
    existing = db.scalar(select(User).where(User.email == intake.email))
    if existing is not None:
        return existing
    return create_user(
        db,
        payload=_UserPayload(
            email=intake.email,
            password="TempPass#12345",
            name=_safe_username_from_full_name(intake.full_name),
        ),
    )


def start_engine_for_intake(
    db: Session,
    *,
    intake_id: int,
    started_by: str,
    interval_minutes: int,
    plan_name: str,
    run_now: bool,
) -> tuple[CustomerIntake, object | None, object]:
    intake = get_customer_intake(db, intake_id=intake_id)
    if intake.payment_status != "paid":
        raise ValueError("Payment is not confirmed yet for this intake")

    user = _user_for_intake(db, intake)
    plan, run, _ = bootstrap_daily_mode(
        db=db,
        user_id=user.id,
        video_id=None,
        niche=intake.niche,
        audience=intake.target_customer_profile[:200],
        objective=intake.primary_kpi,
        problem_angle=intake.pain_point[:255],
        offer=f"{intake.product_name} | {intake.product_price_range}",
        platform=intake.main_platforms.split(",")[0].strip().lower() if intake.main_platforms else "tiktok",
        region=intake.target_region[:100],
        interval_minutes=interval_minutes,
        plan_name=plan_name,
        seed_text=f"{intake.product_name} {intake.niche}",
        leads_count=max(1, min(20, intake.current_monthly_leads // 20 if intake.current_monthly_leads else 8)),
        variants_count=3,
        run_now=run_now,
    )

    intake.mark_engine_started(
        plan_id=plan.id,
        run_id=run.id if run else None,
        started_by=started_by,
    )
    intake.status = "engine_started"
    db.commit()
    db.refresh(intake)
    return intake, run, plan
