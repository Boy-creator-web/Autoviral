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
