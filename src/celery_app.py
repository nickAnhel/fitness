from celery import Celery

from src.config import settings


celery_app = Celery(
    "fitness",
    broker=settings.celery.broker_url,
    backend=settings.celery.result_backend,
    include=["src.notifications.tasks"],
)

celery_app.conf.update(
    task_default_queue=settings.celery.default_queue,
    timezone=settings.celery.timezone,
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)

