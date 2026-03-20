from datetime import datetime
from typing import Any

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


class ScraperAnalyzeRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=255)
    competitor_signals: list[str] = Field(default_factory=list)
    competitor_videos: list[str] = Field(default_factory=list)
    competitor_comments: list[str] = Field(default_factory=list)
    competitor_posts: list[str] = Field(default_factory=list)
    trend_points: list[float] = Field(default_factory=list)
    forum_signals: list[str] = Field(default_factory=list)
    user_actions: list[str] = Field(default_factory=list)
    user_text_signals: list[str] = Field(default_factory=list)
    comments: list[str] = Field(default_factory=list)
    competitor_contents: list[str] = Field(default_factory=list)
    audience_questions: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)
    lead_signals: list[str] = Field(default_factory=list)
    user_activity_logs: list[str] = Field(default_factory=list)


class ScraperAnalyzeResponse(BaseModel):
    job_id: str
    status: str
    results: list[ScraperDataRead] = Field(default_factory=list)


class ScraperJobStatusResponse(BaseModel):
    job_id: str
    state: str
    meta: dict | None = None
    result: dict | None = None
    error: str | None = None


class ScraperInsightSummaryResponse(BaseModel):
    topic: str | None = None
    total_insights: int
    by_source: dict[str, dict[str, float | int]]
    high_intent_users: list[dict[str, str | float]] = Field(default_factory=list)
    missed_topics: list[str] = Field(default_factory=list)
    unanswered_questions: list[str] = Field(default_factory=list)
    emotion_overview: dict[str, int] = Field(default_factory=dict)
    latest_features: list[dict[str, Any]] = Field(default_factory=list)


class HumanCreateRequest(BaseModel):
    user_id: int
    name: str = Field(min_length=1, max_length=255)
    age: int = Field(ge=0, le=120)
    gender: str = Field(min_length=1, max_length=50)
    style: str = Field(min_length=1, max_length=100)
    prompt: str = Field(min_length=1)


class HumanTrainRequest(BaseModel):
    human_id: int
    user_photos: list[str] = Field(min_length=1)


class HumanTrainResponse(BaseModel):
    message: str
    human: SyntheticHumanRead


class VideoGenerateRequest(BaseModel):
    user_id: int
    human_id: int
    title: str = Field(min_length=1, max_length=255)
    script: str = Field(min_length=1)
    duration: int = Field(gt=0, le=3600)


class VideoSwapFaceRequest(BaseModel):
    user_id: int
    human_id: int
    title: str = Field(min_length=1, max_length=255)
    source_face: str = Field(min_length=1)
    target_video: str = Field(min_length=1)


class VideoLipSyncRequest(BaseModel):
    user_id: int
    human_id: int
    title: str = Field(min_length=1, max_length=255)
    video_path: str = Field(min_length=1)
    audio_path: str = Field(min_length=1)


class VideoJobQueuedResponse(BaseModel):
    job_id: str
    video: VideoRead
    status: str


class VideoJobStatusResponse(BaseModel):
    job_id: str
    state: str
    video_id: int | None = None
    video_status: str | None = None
    file_path: str | None = None
    result: dict | None = None
    error: str | None = None
