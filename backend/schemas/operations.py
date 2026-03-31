"""Operational schemas for actions, reports, and results."""

from pydantic import BaseModel, Field


class CampaignActionCreate(BaseModel):
    user_id: int
    action_type: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=255)
    payload: str = Field(default="{}")


class CampaignActionRead(BaseModel):
    id: int
    user_id: int
    action_type: str
    title: str
    payload: str
    status: str


class CampaignResultCreate(BaseModel):
    action_id: int
    summary: str = Field(min_length=1, max_length=255)
    result_data: str = Field(default="{}")


class CampaignResultRead(BaseModel):
    id: int
    action_id: int
    summary: str
    result_data: str
    status: str


class CampaignReportCreate(BaseModel):
    user_id: int
    period: str = Field(min_length=1, max_length=100)
    report_data: str = Field(default="{}")


class CampaignReportRead(BaseModel):
    id: int
    user_id: int
    period: str
    report_data: str
    status: str
