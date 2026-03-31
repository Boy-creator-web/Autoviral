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
    redis_url: str = "redis://redis:6379/0"
    rate_limit_requests: int = 120
    rate_limit_window_seconds: int = 60
    login_fail_max_attempts: int = 5
    login_fail_window_seconds: int = 300
    login_lock_seconds: int = 900
    monitor_interval_seconds: int = 300
    backup_dir: str = "/root/autoviral/backups"
    backup_stale_minutes: int = 1440

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
