"""Application settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "Autoviral Backend"
    api_v1_prefix: str = "/api/v1"
    # Local default uses SQLite for easy bootstrapping.
    # Production can override via DATABASE_URL (docker-compose uses PostgreSQL).
    database_url: str = "sqlite:///./autoviral.db"
    secret_key: str = "change-me-autoviral-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    payment_webhook_secret: str = "change-me-webhook-secret"
    allowed_origins: str = "*"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
