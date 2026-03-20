"""Application settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "Autoviral Backend"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg2://autoviral:autoviral@postgres:5432/autoviral"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
