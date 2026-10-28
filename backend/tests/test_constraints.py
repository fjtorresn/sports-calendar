"""The database itself rejects invalid data, not just the API."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import CompetitorExternalRef, Subscription
from app.models.enums import DataSource
from tests.factories import make_competitor, make_event, make_event_kind, make_sport, make_user


def test_subscription_requires_at_least_one_filter(db: Session) -> None:
    user = make_user(db)
    db.add(Subscription(user_id=user.id))

    with pytest.raises(IntegrityError, match="at_least_one_filter"):
        db.flush()


def test_event_status_rejects_unknown_values(db: Session) -> None:
    event = make_event(db, make_event_kind(db, make_sport(db)))

    # Bypass the ORM's enum validation: the CHECK constraint is the last line of defense.
    with pytest.raises(IntegrityError, match="eventstatus"):
        db.execute(text("UPDATE events SET status = 'live' WHERE id = :id"), {"id": event.id})


def test_external_id_is_unique_per_source(db: Session) -> None:
    sport = make_sport(db)
    first, second = make_competitor(db, sport), make_competitor(db, sport)
    db.add(CompetitorExternalRef(competitor_id=first.id, source=DataSource.FOOTBALL_DATA, external_id="81"))
    db.flush()
    db.add(CompetitorExternalRef(competitor_id=second.id, source=DataSource.FOOTBALL_DATA, external_id="81"))

    with pytest.raises(IntegrityError, match="source_external_id"):
        db.flush()


def test_competitor_takes_part_in_an_event_once(db: Session) -> None:
    sport = make_sport(db)
    competitor = make_competitor(db, sport)
    event = make_event(db, make_event_kind(db, sport), participants=(competitor,))

    with pytest.raises(IntegrityError, match="pk_event_participants"):
        db.execute(
            text("INSERT INTO event_participants (event_id, competitor_id) VALUES (:e, :c)"),
            {"e": event.id, "c": competitor.id},
        )


def test_users_get_distinct_ical_tokens(db: Session) -> None:
    first, second = make_user(db), make_user(db)

    assert len(first.ical_token) >= 40
    assert first.ical_token != second.ical_token
