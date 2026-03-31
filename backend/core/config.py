from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "Autoviral Backend"
    api_v1_prefix: str = "/api/v1"
    database_url: str = (
        "postgresql+psycopg2://autoviral:autoviral@postgres:5432/autoviral"
    )
    # Backward-compatibility fields for existing .env deployments.
    redis_url: str = "redis://redis:6379/0"
    scraper_queue_name: str = "scraper_jobs"
    video_queue_name: str = "video_render_jobs"
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/0"
    secret_key: str = "change-this-secret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    docs_enabled: bool = True
    api_key_required: bool = False
    api_key: str = ""
    allowed_hosts_csv: str = ""
    mirofish_base_url: str = "http://localhost:5001"
    mirofish_timeout_seconds: int = 10
    postiz_api_base_url: str = "http://localhost:3000/api/public/v1"
    postiz_api_key: str = ""
    postiz_timeout_seconds: int = 20
    postiz_integration_ids_json: str = (
        '{"tiktok":"","instagram":"","youtube":"","facebook":"","x":"","linkedin":""}'
    )
    autonomous_scheduler_enabled: bool = False
    autonomous_scheduler_tick_seconds: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
