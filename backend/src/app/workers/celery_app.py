"""Celery application and schedule (design.md §5.2, flow A)."""

from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "sports_calendar",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)
celery_app.conf.update(
    timezone="UTC",
    task_acks_late=True,  # if a worker dies mid-task, another one picks it up
    worker_prefetch_multiplier=1,
    beat_schedule={
        # Schedules change slowly; one daily sync is enough (NFR-1).
        "sync-followed-competitions": {
            "task": "app.workers.tasks.sync_followed_competitions",
            "schedule": crontab(hour=4, minute=0),
        },
    },
)
