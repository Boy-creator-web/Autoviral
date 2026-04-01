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


class CustomerIntakeCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    phone: str = Field(min_length=5, max_length=32)
    business_name: str = Field(min_length=1, max_length=180)
    niche: str = Field(min_length=1, max_length=150)
    product_name: str = Field(min_length=1, max_length=180)
    product_category: str = Field(min_length=1, max_length=120)
    product_price_range: str = Field(min_length=1, max_length=120)
    business_model: str = Field(min_length=2, max_length=80)
    target_customer_profile: str = Field(min_length=1, max_length=2000)
    target_region: str = Field(min_length=1, max_length=120)
    main_platforms: str = Field(min_length=1, max_length=255)
    primary_kpi: str = Field(min_length=1, max_length=120)
    current_monthly_leads: int = Field(default=0, ge=0)
    current_conversion_rate_percent: float = Field(default=0.0, ge=0, le=100)
    sales_cycle_days: int = Field(default=0, ge=0)
    monthly_marketing_budget: float = Field(default=0.0, ge=0)
    preferred_contact_time: str = Field(min_length=2, max_length=120)
    monthly_revenue_target: float = Field(default=0.0, ge=0)
    preferred_plan: str = Field(default="starter", min_length=2, max_length=50)
    pain_point: str = Field(min_length=1, max_length=2000)
    desired_outcome: str = Field(min_length=1, max_length=2000)
    source: str = Field(default="website", min_length=2, max_length=120)


class CustomerIntakeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: EmailStr
    phone: str
    business_name: str
    niche: str
    product_name: str
    product_category: str
    product_price_range: str
    business_model: str
    target_customer_profile: str
    target_region: str
    main_platforms: str
    primary_kpi: str
    current_monthly_leads: int
    current_conversion_rate_percent: float
    sales_cycle_days: int
    monthly_marketing_budget: float
    preferred_contact_time: str
    monthly_revenue_target: float
    preferred_plan: str
    pain_point: str
    desired_outcome: str
    source: str
    payment_status: str
    payment_reference: str | None = None
    payment_method: str | None = None
    payment_amount: float
    payment_confirmed_at: datetime | None = None
    engine_status: str
    engine_plan_id: int | None = None
    engine_last_run_id: int | None = None
    engine_started_at: datetime | None = None
    engine_started_by: str | None = None
    status: str
    created_at: datetime


class CustomerIntakeListResponse(BaseModel):
    count: int
    items: list[CustomerIntakeRead]


class CustomerPaymentConfirmRequest(BaseModel):
    intake_id: int
    payment_reference: str = Field(min_length=3, max_length=120)
    payment_method: str = Field(default="midtrans", min_length=2, max_length=80)
    payment_amount: float = Field(ge=0)


class CustomerEngineStartRequest(BaseModel):
    intake_id: int
    started_by: str = Field(default="owner", min_length=2, max_length=120)
    interval_minutes: int = Field(default=1440, ge=15, le=10_080)
    plan_name: str = Field(default="Client Paid - Autonomous Mode", min_length=3, max_length=120)
    run_now: bool = True


class CustomerEngineStartResponse(BaseModel):
    intake: CustomerIntakeRead
    run: dict | None = None
    plan: dict


class CustomerSocialCredentialInput(BaseModel):
    platform: str = Field(min_length=2, max_length=50)
    username: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=255)
    autopost_enabled: bool = True


class CustomerSocialCredentialRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    platform: str
    username: str
    autopost_enabled: bool
    created_at: datetime


class CustomerCheckoutCreateRequest(BaseModel):
    intake_id: int
    payment_method: str = Field(default="midtrans", min_length=2, max_length=80)
    preferred_plan: str = Field(default="growth", min_length=2, max_length=50)
    social_accounts: list[CustomerSocialCredentialInput] = Field(min_length=1, max_length=12)


class CustomerCheckoutCreateResponse(BaseModel):
    intake: CustomerIntakeRead
    social_accounts_count: int
    social_accounts: list[CustomerSocialCredentialRead]


class CustomerAiCsChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    customer_name: str | None = Field(default=None, max_length=120)
    business_name: str | None = Field(default=None, max_length=180)
    email: EmailStr | None = None
    source: str = Field(default="website", min_length=2, max_length=120)


class CustomerAiCsChatResponse(BaseModel):
    reply: str
    suggested_actions: list[str] = Field(default_factory=list)
    suggested_plan: str = Field(default="growth")
    handoff_required: bool = False


class ViralExperimentCreateRequest(BaseModel):
    user_id: int
    video_id: int | None = None
    niche: str = Field(min_length=1, max_length=150)
    audience: str = Field(min_length=1, max_length=200)
    objective: str = Field(min_length=1, max_length=200)
    problem_angle: str = Field(min_length=1, max_length=255)
    offer: str | None = Field(default=None, max_length=255)
    tone: str = Field(default="direct", min_length=3, max_length=80)
    platform: str = Field(default="tiktok", min_length=2, max_length=50)
    trend_context: str | None = Field(default=None, max_length=5000)
    variants_count: int = Field(default=3, ge=2, le=5)


class ViralVariantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    experiment_id: int
    variant_key: str
    hook: str
    script: str
    cta: str
    caption: str
    hashtags: str
    duration_target_sec: int
    predicted_hook_rate: float
    predicted_watch_rate: float
    predicted_share_rate: float
    predicted_save_rate: float
    predicted_score: float


class ViralExperimentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    video_id: int | None
    niche: str
    audience: str
    objective: str
    problem_angle: str
    offer: str | None
    tone: str
    platform: str
    trend_context: str | None
    status: str
    baseline_score: float
    created_at: datetime
    updated_at: datetime


class ViralExperimentCreateResponse(BaseModel):
    experiment: ViralExperimentRead
    variants: list[ViralVariantRead]


class ViralExperimentListResponse(BaseModel):
    count: int
    experiments: list[ViralExperimentRead]


class ViralVariantListResponse(BaseModel):
    count: int
    variants: list[ViralVariantRead]


class ViralMetricIngestRequest(BaseModel):
    impressions: int = Field(ge=0)
    views_3s: int = Field(ge=0)
    views_10s: int = Field(ge=0)
    completions: int = Field(ge=0)
    likes: int = Field(default=0, ge=0)
    comments: int = Field(default=0, ge=0)
    shares: int = Field(default=0, ge=0)
    saves: int = Field(default=0, ge=0)
    profile_visits: int = Field(default=0, ge=0)
    link_clicks: int = Field(default=0, ge=0)
    watch_time_avg_sec: float = Field(default=0.0, ge=0)
    conversion_events: int = Field(default=0, ge=0)


class ViralMetricRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    variant_id: int
    impressions: int
    views_3s: int
    views_10s: int
    completions: int
    likes: int
    comments: int
    shares: int
    saves: int
    profile_visits: int
    link_clicks: int
    watch_time_avg_sec: float
    conversion_events: int
    created_at: datetime


class ViralRecommendationRead(BaseModel):
    experiment_id: int
    winner_variant_id: int | None
    winner_variant_key: str | None = None
    winner_score: float | None = None
    confidence: float | None = None
    metric_breakdown: dict[str, float] = Field(default_factory=dict)
    summary: str
    actions: list[str] = Field(default_factory=list)


class ViralModelTrainResponse(BaseModel):
    snapshot_id: int
    sample_count: int
    mae: float
    feature_count: int
    activated: bool


class ViralPredictRequest(BaseModel):
    objective: str = Field(min_length=1, max_length=200)
    tone: str = Field(default="direct", min_length=3, max_length=80)
    hook: str = Field(min_length=1, max_length=255)
    cta: str = Field(min_length=1, max_length=255)
    niche: str = Field(min_length=1, max_length=150)
    platform: str = Field(default="tiktok", min_length=2, max_length=50)
    duration_target_sec: int = Field(default=30, ge=5, le=180)


class ViralPredictResponse(BaseModel):
    predicted_score: float
    using_model: bool
    model_snapshot_id: int | None = None
    features: dict[str, float] = Field(default_factory=dict)


class ViralModelInfoRead(BaseModel):
    snapshot_id: int
    sample_count: int
    mae: float
    is_active: bool


class AutonomousRunRequest(BaseModel):
    user_id: int
    video_id: int | None = None
    seed_text: str = Field(min_length=1, max_length=500)
    niche: str = Field(min_length=1, max_length=150)
    audience: str = Field(min_length=1, max_length=200)
    objective: str = Field(min_length=1, max_length=200)
    problem_angle: str = Field(min_length=1, max_length=255)
    offer: str | None = Field(default=None, max_length=255)
    tone: str = Field(default="direct", min_length=3, max_length=80)
    platform: str = Field(default="tiktok", min_length=2, max_length=50)
    region: str = Field(default="ID", min_length=2, max_length=100)
    leads_count: int = Field(default=5, ge=1, le=100)
    variants_count: int = Field(default=3, ge=2, le=5)


class AutonomousRunRead(BaseModel):
    id: int
    user_id: int
    video_id: int | None = None
    seed_text: str
    niche: str
    audience: str
    objective: str
    region: str
    platform: str
    status: str
    insight_topic: str | None = None
    experiment_id: int | None = None
    selected_variant_id: int | None = None
    discovered_leads_count: int
    qualified_leads_count: int
    drafted_outreach_count: int
    summary: dict = Field(default_factory=dict)
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class AutonomousRunListResponse(BaseModel):
    count: int
    runs: list[AutonomousRunRead]


class AutonomousDashboardRead(BaseModel):
    total_runs: int
    completed_runs: int
    failed_runs: int
    success_rate: float
    avg_discovered_leads: float
    avg_qualified_leads: float
    avg_drafted_outreach: float
    latest_experiment_ids: list[int] = Field(default_factory=list)


class AutonomousPlanCreateRequest(BaseModel):
    user_id: int
    video_id: int | None = None
    name: str = Field(min_length=1, max_length=120)
    seed_text: str = Field(min_length=1, max_length=500)
    niche: str = Field(min_length=1, max_length=150)
    audience: str = Field(min_length=1, max_length=200)
    objective: str = Field(min_length=1, max_length=200)
    problem_angle: str = Field(min_length=1, max_length=255)
    offer: str | None = Field(default=None, max_length=255)
    tone: str = Field(default="direct", min_length=3, max_length=80)
    platform: str = Field(default="tiktok", min_length=2, max_length=50)
    region: str = Field(default="ID", min_length=2, max_length=100)
    leads_count: int = Field(default=5, ge=1, le=100)
    variants_count: int = Field(default=3, ge=2, le=5)
    interval_minutes: int = Field(default=360, ge=1, le=10_080)
    is_active: bool = True


class AutonomousPlanSetActiveRequest(BaseModel):
    is_active: bool


class AutonomousPlanRead(BaseModel):
    id: int
    user_id: int
    video_id: int | None = None
    name: str
    seed_text: str
    niche: str
    audience: str
    objective: str
    problem_angle: str
    offer: str | None = None
    tone: str
    platform: str
    region: str
    leads_count: int
    variants_count: int
    interval_minutes: int
    is_active: bool
    next_run_at: datetime | None = None
    last_run_at: datetime | None = None
    last_status: str | None = None
    last_error: str | None = None
    created_at: datetime
    updated_at: datetime


class AutonomousPlanListResponse(BaseModel):
    count: int
    plans: list[AutonomousPlanRead]


class AutonomousSchedulerTickResponse(BaseModel):
    executed_runs: int
    run_ids: list[int] = Field(default_factory=list)


class DailyOpsBootstrapRequest(BaseModel):
    user_id: int
    video_id: int | None = None
    niche: str = Field(min_length=1, max_length=150)
    audience: str = Field(min_length=1, max_length=200)
    objective: str = Field(default="increase sales leads", min_length=1, max_length=200)
    region: str = Field(default="ID", min_length=2, max_length=100)


class DailyOpsBootstrapResponse(BaseModel):
    quick_run_id: int
    quick_run_status: str
    created_plan_ids: list[int] = Field(default_factory=list)
    existing_plan_count: int
    total_plan_count: int
    ml_training_status: str
    ml_snapshot_id: int | None = None


class AutonomousDailyModeRequest(BaseModel):
    user_id: int
    video_id: int | None = None
    niche: str = Field(min_length=1, max_length=150)
    audience: str = Field(min_length=1, max_length=200)
    objective: str = Field(min_length=1, max_length=200)
    problem_angle: str = Field(min_length=1, max_length=255)
    offer: str | None = Field(default=None, max_length=255)
    platform: str = Field(default="tiktok", min_length=2, max_length=50)
    region: str = Field(default="ID", min_length=2, max_length=100)
    interval_minutes: int = Field(default=1_440, ge=15, le=10_080)
    plan_name: str = Field(default="Daily Autonomous Mode", min_length=3, max_length=120)
    seed_text: str | None = Field(default=None, max_length=500)
    leads_count: int = Field(default=8, ge=1, le=100)
    variants_count: int = Field(default=3, ge=2, le=5)
    run_now: bool = True


class AutonomousDailyModeResponse(BaseModel):
    plan: AutonomousPlanRead
    run: AutonomousRunRead | None = None
    scheduler_enabled: bool
    ml_status: str
