"""Celery application.

For now it only exists so the worker starts; ingestion tasks arrive in phase 3.
"""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery("sports_calendar", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    timezone="UTC",
    task_acks_late=True,  # if a worker dies mid-task, another one picks it up
    worker_prefetch_multiplier=1,
)
