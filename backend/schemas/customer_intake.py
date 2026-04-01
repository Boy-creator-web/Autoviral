"""Schemas for public customer intake form."""

from pydantic import BaseModel, EmailStr, Field


class CustomerIntakeCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    phone: str = Field(default="", max_length=50)
    business_name: str = Field(default="", max_length=255)
    niche: str = Field(default="", max_length=255)
    monthly_revenue_target: float = Field(default=0, ge=0)
    preferred_plan: str = Field(default="starter", max_length=100)
    pain_point: str = Field(default="", max_length=2000)
    desired_outcome: str = Field(default="", max_length=2000)
    source: str = Field(default="website", max_length=255)


class CustomerIntakeRead(BaseModel):
    id: int
    full_name: str
    email: str
    phone: str
    business_name: str
    niche: str
    monthly_revenue_target: float
    preferred_plan: str
    pain_point: str
    desired_outcome: str
    source: str
    status: str
