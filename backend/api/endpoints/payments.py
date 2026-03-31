"""Payments endpoint."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException, status

from core.database import get_db
from models.payment import Payment
from models.subscription import Subscription
from models.user import User
from schemas.billing import PaymentCreate, PaymentRead

router = APIRouter()


def _new_invoice_no(user_id: int) -> str:
    return f"INV-{user_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"


@router.get("/", response_model=list[PaymentRead])
def list_payments(db: Session = Depends(get_db)) -> list[PaymentRead]:
    rows = list(db.scalars(select(Payment).order_by(Payment.id.desc())).all())
    return [
        PaymentRead(
            id=row.id,
            user_id=row.user_id,
            subscription_id=row.subscription_id,
            amount=row.amount,
            currency=row.currency,
            status=row.status,
            provider=row.provider,
            invoice_no=row.invoice_no,
        )
        for row in rows
    ]


@router.post("/", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
def create_payment(payload: PaymentCreate, db: Session = Depends(get_db)) -> PaymentRead:
    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if payload.subscription_id is not None:
        subscription = db.get(Subscription, payload.subscription_id)
        if subscription is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

    row = Payment(
        user_id=payload.user_id,
        subscription_id=payload.subscription_id,
        amount=payload.amount,
        currency="IDR",
        status="paid",
        provider=payload.provider,
        invoice_no=_new_invoice_no(payload.user_id),
    )
    db.add(row)

    if payload.subscription_id is not None:
        subscription = db.get(Subscription, payload.subscription_id)
        if subscription is not None:
            subscription.status = "active"
            db.add(subscription)

    db.commit()
    db.refresh(row)
    return PaymentRead(
        id=row.id,
        user_id=row.user_id,
        subscription_id=row.subscription_id,
        amount=row.amount,
        currency=row.currency,
        status=row.status,
        provider=row.provider,
        invoice_no=row.invoice_no,
    )
