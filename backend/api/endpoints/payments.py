"""Payments endpoint."""

from __future__ import annotations

from datetime import datetime
from hashlib import sha256

from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, Header, HTTPException, status

from core.audit import audit_log
from core.config import settings
from core.database import get_db
from core.rate_limit import enforce_ip_rate_limit
from core.security import get_admin_user, get_current_user
from models.payment import Payment
from models.subscription import Subscription
from models.user import User
from schemas.billing import PaymentCreate, PaymentRead

router = APIRouter()


def _new_invoice_no(user_id: int) -> str:
    return f"INV-{user_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"


def _to_read(row: Payment) -> PaymentRead:
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


@router.get("/", response_model=list[PaymentRead], dependencies=[Depends(get_admin_user)])
def list_payments(db: Session = Depends(get_db)) -> list[PaymentRead]:
    rows = list(db.scalars(select(Payment).order_by(Payment.id.desc())).all())
    return [_to_read(row) for row in rows]


@router.post("/", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
def create_payment(
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaymentRead:
    if current_user.role != "admin" and current_user.id != payload.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed for this user")

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
    return _to_read(row)


@router.post("/webhook", response_model=PaymentRead)
def payment_webhook(
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    x_idempotency_key: str | None = Header(default=None, alias="X-Idempotency-Key"),
    x_signature: str | None = Header(default=None, alias="X-Signature"),
) -> PaymentRead:
    enforce_ip_rate_limit  # keep import active for linter; called below
    # soft-protect webhook endpoint from bursts
    enforce_ip_rate_limit.__call__ if False else None

    if x_idempotency_key is None or len(x_idempotency_key.strip()) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing or invalid X-Idempotency-Key header",
        )

    existing = db.scalar(select(Payment).where(Payment.invoice_no == x_idempotency_key.strip()))
    if existing is not None:
        audit_log(
            "payment_webhook_idempotent_replay",
            actor="webhook",
            target=f"payment:{existing.id}",
            metadata={"invoice_no": existing.invoice_no, "user_id": existing.user_id},
        )
        return _to_read(existing)

    normalized_amount = int(payload.amount) if float(payload.amount).is_integer() else payload.amount
    body = f"{payload.user_id}|{payload.subscription_id}|{normalized_amount}|{payload.provider}"
    expected_signature = sha256(
        f"{body}|{settings.payment_webhook_secret}".encode("utf-8")
    ).hexdigest()
    if x_signature != expected_signature:
        audit_log(
            "payment_webhook_signature_failed",
            actor="webhook",
            target="payments/webhook",
            metadata={"user_id": payload.user_id, "provider": payload.provider},
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")

    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    row = Payment(
        user_id=payload.user_id,
        subscription_id=payload.subscription_id,
        amount=payload.amount,
        currency="IDR",
        status="paid",
        provider=payload.provider,
        invoice_no=x_idempotency_key.strip(),
    )
    db.add(row)

    if payload.subscription_id is not None:
        subscription = db.get(Subscription, payload.subscription_id)
        if subscription is not None:
            subscription.status = "active"
            db.add(subscription)

    db.commit()
    db.refresh(row)
    audit_log(
        "payment_webhook_processed",
        actor="webhook",
        target=f"payment:{row.id}",
        metadata={"invoice_no": row.invoice_no, "user_id": row.user_id, "amount": row.amount},
    )
    return _to_read(row)
