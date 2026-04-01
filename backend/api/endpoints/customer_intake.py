"""Public customer intake endpoint for website request form."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from core.audit import audit_log
from core.database import get_db
from core.rate_limit import apply_rate_limit_headers, enforce_ip_rate_limit
from models.customer_intake import CustomerIntake
from schemas.customer_intake import CustomerIntakeCreate, CustomerIntakeRead

router = APIRouter()


def _to_read(row: CustomerIntake) -> CustomerIntakeRead:
    return CustomerIntakeRead(
        id=row.id,
        full_name=row.full_name,
        email=row.email,
        phone=row.phone,
        business_name=row.business_name,
        niche=row.niche,
        monthly_revenue_target=row.monthly_revenue_target,
        preferred_plan=row.preferred_plan,
        pain_point=row.pain_point,
        desired_outcome=row.desired_outcome,
        source=row.source,
        status=row.status,
    )


@router.post("/", response_model=CustomerIntakeRead, status_code=status.HTTP_201_CREATED)
def create_customer_intake(
    payload: CustomerIntakeCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> CustomerIntakeRead:
    ip_limit = enforce_ip_rate_limit(request)
    apply_rate_limit_headers(response, ip_limit)

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

    audit_log(
        "customer_intake_created",
        actor=payload.email,
        target=f"customer_intake:{row.id}",
        metadata={"preferred_plan": payload.preferred_plan, "source": payload.source},
        db=db,
    )
    return _to_read(row)
