"""Turn provider DTOs into rows: resolve identities, upsert, record sync state (design.md §5.2 A)."""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.ingestion.base import CompetitorData, EventData, EventProvider
from app.models import (
    Competition,
    CompetitionExternalRef,
    Competitor,
    CompetitorExternalRef,
    Event,
    EventExternalRef,
    EventKind,
    EventParticipant,
    SyncState,
)
from app.models.enums import DataSource, SyncStatus

logger = logging.getLogger(__name__)


class SyncError(Exception):
    """A competition could not be synced; the failure is recorded in sync_state."""


@dataclass
class SyncResult:
    created: int = 0
    updated: int = 0
    unchanged: int = 0
    skipped: int = 0


def sync_competition(db: Session, competition: Competition, provider: EventProvider) -> SyncResult:
    """Fetch the competition's events from ``provider`` and upsert them.

    Idempotent: running it twice with the same source data changes nothing. Data changes
    happen inside a savepoint, so a failure leaves earlier rows untouched while the
    failure itself is still recorded in ``sync_state``. The caller owns the commit.
    """
    ref = db.scalar(
        select(CompetitionExternalRef).where(
            CompetitionExternalRef.competition_id == competition.id,
            CompetitionExternalRef.source == provider.source,
        )
    )
    if ref is None:
        raise SyncError(f"{competition.slug} has no {provider.source} reference")

    state = _sync_state(db, competition, provider.source)
    try:
        with db.begin_nested():
            result = _apply(db, competition, provider.source, provider.fetch_events(ref.external_id))
    except Exception as exc:
        state.last_status, state.last_error = SyncStatus.FAILED, str(exc)[:2000]
        db.flush()
        raise SyncError(f"syncing {competition.slug} from {provider.source} failed: {exc}") from exc

    state.last_status, state.last_error, state.last_synced_at = SyncStatus.SUCCESS, None, datetime.now(UTC)
    db.flush()
    logger.info("Synced %s from %s: %s", competition.slug, provider.source, result)
    return result


def _sync_state(db: Session, competition: Competition, source: DataSource) -> SyncState:
    state = db.scalar(select(SyncState).where(SyncState.competition_id == competition.id, SyncState.source == source))
    if state is None:
        state = SyncState(competition_id=competition.id, source=source)
        db.add(state)
    return state


def _apply(db: Session, competition: Competition, source: DataSource, events: list[EventData]) -> SyncResult:
    kinds = dict(
        db.execute(select(EventKind.slug, EventKind.id).where(EventKind.sport_id == competition.sport_id)).all()
    )
    competitors = _resolve_competitors(db, competition, source, events)
    existing = _existing_events(db, source, [e.external_id for e in events])

    result = SyncResult()
    for data in events:
        kind_id = kinds.get(data.event_kind)
        if kind_id is None:
            logger.warning("Skipping %s: unknown event kind %r", data.external_id, data.event_kind)
            result.skipped += 1
            continue

        fields = {
            "sport_id": competition.sport_id,
            "competition_id": competition.id,
            "event_kind_id": kind_id,
            "title": data.title,
            "start_time": data.start_time,
            "time_precision": data.time_precision,
            "status": data.status,
            "venue": data.venue,
        }
        participants = {competitors[p.competitor.external_id].id: p.is_home for p in data.participants}

        event = existing.get(data.external_id)
        if event is None:
            event = Event(**fields)
            db.add(event)
            db.flush()
            db.add(EventExternalRef(event_id=event.id, source=source, external_id=data.external_id))
            _set_participants(event, participants)
            result.created += 1
        # `|`, not `or`: both updates must run even when the first one reports a change.
        elif _update(event, fields) | _set_participants(event, participants):
            result.updated += 1
        else:
            result.unchanged += 1
    return result


def _resolve_competitors(
    db: Session, competition: Competition, source: DataSource, events: list[EventData]
) -> dict[str, Competitor]:
    """Map each source competitor id to our Competitor, creating the ones we haven't seen."""
    wanted: dict[str, CompetitorData] = {
        p.competitor.external_id: p.competitor for e in events for p in e.participants
    }
    if not wanted:
        return {}

    rows = db.execute(
        select(CompetitorExternalRef.external_id, Competitor)
        .join(Competitor)
        .where(CompetitorExternalRef.source == source, CompetitorExternalRef.external_id.in_(wanted))
    ).all()
    found = {external_id: competitor for external_id, competitor in rows}

    for external_id, data in wanted.items():
        competitor = found.get(external_id)
        if competitor is None:
            competitor = Competitor(sport_id=competition.sport_id, kind=data.kind, name=data.name)
            db.add(competitor)
            db.flush()
            db.add(CompetitorExternalRef(competitor_id=competitor.id, source=source, external_id=external_id))
            found[external_id] = competitor
        competitor.name, competitor.short_name = data.name, data.short_name
    return found


def _existing_events(db: Session, source: DataSource, external_ids: list[str]) -> dict[str, Event]:
    if not external_ids:
        return {}
    rows = db.execute(
        select(EventExternalRef.external_id, Event)
        .join(Event)
        .where(EventExternalRef.source == source, EventExternalRef.external_id.in_(external_ids))
        .options(selectinload(Event.participants))
    ).all()
    return {external_id: event for external_id, event in rows}


def _update(event: Event, fields: dict) -> bool:
    changed = False
    for name, value in fields.items():
        if getattr(event, name) != value:
            setattr(event, name, value)
            changed = True
    return changed


def _set_participants(event: Event, wanted: dict[int, bool | None]) -> bool:
    """Make the event's participants match ``wanted`` (competitor id -> is_home), in place.

    Rows are edited rather than replaced: deleting and re-inserting the same composite
    primary key in one flush could collide.
    """
    current = {p.competitor_id: p for p in event.participants}
    changed = False
    for competitor_id, participant in current.items():
        if competitor_id not in wanted:
            event.participants.remove(participant)
            changed = True
        elif participant.is_home != wanted[competitor_id]:
            participant.is_home = wanted[competitor_id]
            changed = True
    for competitor_id, is_home in wanted.items():
        if competitor_id not in current:
            event.participants.append(EventParticipant(competitor_id=competitor_id, is_home=is_home))
            changed = True
    return changed
