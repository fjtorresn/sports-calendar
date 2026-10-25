"""Which competitions to sync, and syncing one from all of its sources.

Shared by the CLI (``app.scripts.sync``) and the Celery tasks, so both behave the same.
"""

from sqlalchemy import select, union
from sqlalchemy.orm import Session

from app.ingestion.registry import get_provider
from app.ingestion.sync import SyncResult, sync_competition
from app.models import (
    Competition,
    CompetitionExternalRef,
    Competitor,
    Event,
    EventParticipant,
    Subscription,
)
from app.models.enums import DataSource


def followed_competition_ids(db: Session) -> set[int]:
    """Competitions with at least one direct or indirect subscriber (on-demand ingestion, design.md §3.3).

    Indirect: a followed sport pulls in all its competitions; a followed competitor or
    nation pulls in the competitions where it already has events.
    """
    direct = select(Subscription.competition_id).where(Subscription.competition_id.is_not(None))
    by_sport = select(Competition.id).join(Subscription, Subscription.sport_id == Competition.sport_id)
    by_competitor = (
        select(Event.competition_id)
        .join(EventParticipant)
        .join(Subscription, Subscription.competitor_id == EventParticipant.competitor_id)
    )
    by_nation = (
        select(Event.competition_id)
        .join(EventParticipant)
        .join(Competitor)
        .join(Subscription, Subscription.nation_id == Competitor.nation_id)
    )
    rows = db.scalars(union(direct, by_sport, by_competitor, by_nation))
    return {competition_id for competition_id in rows if competition_id is not None}


def syncable_competition_ids(db: Session) -> set[int]:
    """Every competition that has at least one data source."""
    return set(db.scalars(select(CompetitionExternalRef.competition_id).distinct()))


def sync_from_all_sources(db: Session, competition: Competition) -> dict[DataSource, SyncResult]:
    sources = db.scalars(
        select(CompetitionExternalRef.source).where(CompetitionExternalRef.competition_id == competition.id)
    )
    return {source: sync_competition(db, competition, get_provider(source)) for source in sources}
