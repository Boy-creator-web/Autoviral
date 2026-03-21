"""Celery application configuration for asynchronous video and scraper jobs."""

from celery import Celery

from core.config import settings

celery_app = Celery(
    "autoviral",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["services.video.tasks", "services.scraper.tasks", "services.runpod.tasks"],
)

celery_app.conf.update(
    task_default_queue=settings.video_queue_name,
    task_track_started=True,
)
