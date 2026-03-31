"""Billing schemas for pricing, subscriptions, and payments."""

from pydantic import BaseModel, Field


class PricingPlanRead(BaseModel):
    id: int
    code: str
    name: str
    description: str
    price_monthly: float
    video_quota: int
    campaign_quota: int
    scraper_quota: int
    active: bool


class SubscriptionCreate(BaseModel):
    user_id: int
    plan_id: int
    months: int = Field(default=1, ge=1, le=24)


class SubscriptionRead(BaseModel):
    id: int
    user_id: int
    plan_id: int
    status: str
    start_date: str
    end_date: str


class PaymentCreate(BaseModel):
    user_id: int
    subscription_id: int | None = None
    amount: float = Field(gt=0)
    provider: str = Field(default="manual", min_length=1, max_length=100)


class PaymentRead(BaseModel):
    id: int
    user_id: int
    subscription_id: int | None
    amount: float
    currency: str
    status: str
    provider: str
    invoice_no: str
