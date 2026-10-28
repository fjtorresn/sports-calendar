from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ingestion.base import CompetitorData, EventData, ParticipantData
from app.ingestion.sync import SyncError, sync_competition
from app.models import Competition, CompetitionExternalRef, Competitor, Event, SyncState
from app.models.enums import DataSource, EventStatus, SyncStatus, TimePrecision
from tests.factories import make_competition, make_event_kind, make_sport

BARCA = CompetitorData(external_id="81", name="FC Barcelona", short_name="Barça")
INTER = CompetitorData(external_id="108", name="FC Internazionale Milano", short_name="Inter")
KICK_OFF = datetime(2026, 11, 4, 20, 0, tzinfo=UTC)

MATCH = EventData(
    external_id="5001",
    event_kind="match",
    title="Barça vs Inter",
    start_time=KICK_OFF,
    time_precision=TimePrecision.EXACT,
    participants=(ParticipantData(BARCA, is_home=True), ParticipantData(INTER, is_home=False)),
)


class FakeProvider:
    source = DataSource.FOOTBALL_DATA

    def __init__(self, events: list[EventData] | None = None, error: Exception | None = None) -> None:
        self.events = events or []
        self.error = error

    def fetch_events(self, competition_external_id: str) -> list[EventData]:
        if self.error:
            raise self.error
        return self.events


@pytest.fixture
def competition(db: Session) -> Competition:
    sport = make_sport(db)
    make_event_kind(db, sport, "match")
    competition = make_competition(db, sport, "Champions League")
    db.add(CompetitionExternalRef(competition_id=competition.id, source=DataSource.FOOTBALL_DATA, external_id="CL"))
    db.flush()
    return competition


def count(db: Session, model: type) -> int:
    return db.scalar(select(func.count()).select_from(model))


def test_first_sync_creates_events_and_competitors(db: Session, competition: Competition) -> None:
    result = sync_competition(db, competition, FakeProvider([MATCH]))

    assert (result.created, count(db, Event), count(db, Competitor)) == (1, 1, 2)
    event = db.scalar(select(Event))
    assert {p.competitor.name: p.is_home for p in event.participants} == {
        "FC Barcelona": True,
        "FC Internazionale Milano": False,
    }


def test_sync_is_idempotent(db: Session, competition: Competition) -> None:
    provider = FakeProvider([MATCH])
    sync_competition(db, competition, provider)

    result = sync_competition(db, competition, provider)

    assert (result.created, result.updated, result.unchanged) == (0, 0, 1)
    assert (count(db, Event), count(db, Competitor)) == (1, 2)


def test_rescheduled_match_updates_the_same_event(db: Session, competition: Competition) -> None:
    provider = FakeProvider([MATCH])
    sync_competition(db, competition, provider)
    event_id = db.scalar(select(Event.id))

    provider.events = [replace(MATCH, start_time=KICK_OFF + timedelta(days=1), status=EventStatus.POSTPONED)]
    result = sync_competition(db, competition, provider)

    event = db.get(Event, event_id)
    assert result.updated == 1
    assert (event.start_time, event.status) == (KICK_OFF + timedelta(days=1), EventStatus.POSTPONED)
    assert count(db, Event) == 1


def test_competitors_are_shared_across_competitions(db: Session, competition: Competition) -> None:
    other = make_competition(db, competition.sport, "LaLiga")
    db.add(CompetitionExternalRef(competition_id=other.id, source=DataSource.FOOTBALL_DATA, external_id="PD"))
    sync_competition(db, competition, FakeProvider([MATCH]))

    sync_competition(db, other, FakeProvider([replace(MATCH, external_id="7001")]))

    assert (count(db, Event), count(db, Competitor)) == (2, 2)


def test_unknown_event_kind_is_skipped(db: Session, competition: Competition) -> None:
    result = sync_competition(db, competition, FakeProvider([replace(MATCH, event_kind="penalty-shootout")]))

    assert (result.skipped, count(db, Event)) == (1, 0)


def test_success_is_recorded_in_sync_state(db: Session, competition: Competition) -> None:
    sync_competition(db, competition, FakeProvider([MATCH]))

    state = db.scalar(select(SyncState))
    assert state.last_status == SyncStatus.SUCCESS
    assert state.last_synced_at is not None


def test_failure_is_recorded_and_leaves_data_untouched(db: Session, competition: Competition) -> None:
    sync_competition(db, competition, FakeProvider([MATCH]))
    last_success = db.scalar(select(SyncState.last_synced_at))

    with pytest.raises(SyncError, match="boom"):
        sync_competition(db, competition, FakeProvider(error=RuntimeError("boom")))

    state = db.scalar(select(SyncState))
    assert (state.last_status, state.last_error, state.last_synced_at) == (SyncStatus.FAILED, "boom", last_success)
    assert count(db, Event) == 1


def test_competition_without_source_reference_fails_fast(db: Session) -> None:
    sport = make_sport(db)
    orphan = make_competition(db, sport)

    with pytest.raises(SyncError, match="no football_data reference"):
        sync_competition(db, orphan, FakeProvider([MATCH]))
