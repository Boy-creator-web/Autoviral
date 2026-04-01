from celery import Celery

from core.config import settings


def _build_celery_app() -> Celery:
    app = Celery(
        "autoviral",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
    )
    app.conf.update(
        task_default_queue="default",
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        task_routes={
            "autoviral.tasks.run_autonomous_cycle": {"queue": settings.scraper_queue_name},
        },
    )
    app.autodiscover_tasks(["services"], force=True)
    return app


celery_app = _build_celery_app()
