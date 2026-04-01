from celery import Celery

from celery_app import celery_app
from services.tasks import celery_healthcheck_task


def test_celery_app_configuration() -> None:
    assert isinstance(celery_app, Celery)
    assert celery_app.conf.broker_url
    assert celery_app.conf.result_backend
    routes = celery_app.conf.task_routes or {}
    assert "autoviral.tasks.run_autonomous_cycle" in routes


def test_celery_healthcheck_task_runs_locally() -> None:
    payload = celery_healthcheck_task()
    assert payload["ok"] is True
    assert payload["service"] == "celery"
