from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "Autoviral Backend"
    api_v1_prefix: str = "/api/v1"
    database_url: str = (
        "postgresql+psycopg2://autoviral:autoviral@postgres:5432/autoviral"
    )
    redis_url: str = "redis://redis:6379/0"
    scraper_queue_name: str = "scraper_jobs"
    video_queue_name: str = "video_render_jobs"
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/0"
    runpod_api_key: str = "xxx"
    runpod_endpoint_id: str = "xxx"
    secret_key: str = "change-this-secret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
