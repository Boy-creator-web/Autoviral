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
