"""Aplicación de Celery.

Por ahora solo existe para que el worker arranque; las tareas de ingesta llegan en la fase 3.
"""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery("sports_calendar", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    timezone="UTC",
    task_acks_late=True,  # si un worker muere a mitad de una tarea, otra la retoma
    worker_prefetch_multiplier=1,
)
