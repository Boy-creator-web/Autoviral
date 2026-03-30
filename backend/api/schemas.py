from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=255)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    name: str
    created_at: datetime


class SyntheticHumanCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    age: int = Field(ge=0, le=120)
    gender: str = Field(min_length=1, max_length=50)
    style: str = Field(min_length=1, max_length=100)
    user_id: int


class SyntheticHumanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    age: int
    gender: str
    style: str
    user_id: int


class VideoCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    status: str = Field(default="pending", min_length=1, max_length=50)
    file_path: str | None = Field(default=None, max_length=500)
    human_id: int
    user_id: int
    auto_publish_platforms: list[str] = Field(default_factory=list)
    caption: str | None = Field(default=None, max_length=5000)
    tags: list[str] = Field(default_factory=list)


class VideoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    status: str
    file_path: str | None
    human_id: int
    user_id: int


class ScraperDataCreate(BaseModel):
    source: str = Field(min_length=1, max_length=255)
    topic: str = Field(min_length=1, max_length=255)
    intent_score: float = Field(ge=0, le=1)
    raw_data: str = Field(min_length=1)


class ScraperDataRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    topic: str
    intent_score: float
    raw_data: str


class ScraperInsightRequest(BaseModel):
    seed_text: str = Field(min_length=1, max_length=500)
    product_data: dict = Field(default_factory=dict)


class ScraperInsightRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    topic: str
    intent_score: float
    raw_data: str


class ScraperInsightGenerateResponse(BaseModel):
    id: int
    source: str
    topic: str
    intent_score: float
    raw_data: str


class SalesLeadDiscoverRequest(BaseModel):
    industry: str = Field(min_length=1, max_length=150)
    region: str = Field(default="ID", min_length=2, max_length=32)
    company_size: str = Field(default="smb", min_length=2, max_length=50)
    count: int = Field(default=10, ge=1, le=50)


class SalesLeadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    company_name: str
    company_domain: str
    contact_name: str
    contact_title: str
    contact_email: str
    company_size: str
    geography: str
    industry: str
    pain_points_json: str
    raw_signals_json: str
    icp_score: float
    intent_score: float
    priority_score: float
    outreach_status: str
    outreach_draft: str | None = None
    created_at: datetime


class SalesLeadScoreRequest(BaseModel):
    icp_industry: str = Field(min_length=1, max_length=150)
    icp_region: str = Field(default="ID", min_length=2, max_length=32)


class SalesLeadScoreResponse(BaseModel):
    lead: SalesLeadRead


class SalesOutreachDraftRequest(BaseModel):
    channel: str = Field(default="email", min_length=2, max_length=32)


class SalesOutreachDraftResponse(BaseModel):
    lead: SalesLeadRead
    draft: dict[str, str]


class SalesPipelineListResponse(BaseModel):
    count: int
    leads: list[SalesLeadRead]
