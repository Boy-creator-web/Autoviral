from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from api.schemas import CustomerIntakeCreate
from models.customer_intake import CustomerIntake


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
