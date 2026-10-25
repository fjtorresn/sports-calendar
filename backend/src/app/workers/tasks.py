import logging

from redis import Redis

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.ingestion.base import ProviderError
from app.ingestion.runner import followed_competition_ids, sync_from_all_sources
from app.ingestion.sync import SyncError
from app.models import Competition
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

LOCK_TIMEOUT_SECONDS = 15 * 60


@celery_app.task
def sync_followed_competitions() -> int:
    """Fan out: one task per followed competition, so one slow source doesn't block the rest."""
    with SessionLocal() as db:
        ids = followed_competition_ids(db)
    for competition_id in ids:
        sync_competition_task.delay(competition_id)
    return len(ids)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10 * 60)
def sync_competition_task(self, competition_id: int) -> str:
    # Only one sync per competition at a time: the daily run and a new subscription may
    # both enqueue it (design.md §5.2, step A.4). The lock expires on its own if a worker dies.
    redis = Redis.from_url(get_settings().redis_url)
    lock = redis.lock(f"lock:sync-competition:{competition_id}", timeout=LOCK_TIMEOUT_SECONDS, blocking=False)
    if not lock.acquire():
        return "already running"
    try:
        with SessionLocal() as db:
            competition = db.get(Competition, competition_id)
            if competition is None:
                return "competition not found"
            try:
                results = sync_from_all_sources(db, competition)
            except (SyncError, ProviderError) as exc:
                db.commit()  # keep the failure recorded in sync_state
                raise self.retry(exc=exc) from exc
            db.commit()
            return str(results)
    finally:
        lock.release()
