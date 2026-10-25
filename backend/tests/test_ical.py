from datetime import UTC, date, datetime, timedelta

from fastapi.testclient import TestClient
from icalendar import Calendar
from sqlalchemy.orm import Session

from app.models.enums import EventStatus, TimePrecision
from app.services.ical import event_uid
from tests.conftest import MemoryCache
from tests.factories import make_competition, make_event, make_event_kind, make_sport, make_subscription, make_user

SOON = datetime.now(UTC).replace(microsecond=0) + timedelta(days=3)


def feed(client: TestClient, token: str) -> Calendar:
    response = client.get(f"/calendar/{token}.ics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/calendar")
    return Calendar.from_ical(response.content)


def setup_subscription(db: Session):
    sport = make_sport(db)
    kind = make_event_kind(db, sport, "match")
    competition = make_competition(db, sport, "Champions League")
    user = make_user(db)
    make_subscription(db, user, competition_id=competition.id)
    return user, kind, competition


def test_feed_contains_subscribed_events(client: TestClient, db: Session) -> None:
    user, kind, competition = setup_subscription(db)
    event = make_event(db, kind, competition=competition, start_time=SOON, title="Barça vs Inter")

    vevents = feed(client, user.ical_token).walk("VEVENT")

    assert len(vevents) == 1
    item = vevents[0]
    assert str(item["SUMMARY"]) == "Barça vs Inter"
    assert str(item["UID"]) == event_uid(event)
    assert item.decoded("DTSTART") == SOON
    assert item.decoded("DTEND") == SOON + timedelta(hours=2)
    assert "Champions League" in str(item["DESCRIPTION"])


def test_date_only_events_are_all_day(client: TestClient, db: Session) -> None:
    user, kind, competition = setup_subscription(db)
    event = make_event(db, kind, competition=competition, start_time=SOON)
    event.time_precision = TimePrecision.DATE_ONLY
    db.flush()

    item = feed(client, user.ical_token).walk("VEVENT")[0]

    assert item.decoded("DTSTART") == SOON.date()
    assert isinstance(item.decoded("DTSTART"), date) and not isinstance(item.decoded("DTSTART"), datetime)
    assert item.decoded("DTEND") == SOON.date() + timedelta(days=1)


def test_cancelled_and_postponed_events_are_flagged(client: TestClient, db: Session) -> None:
    user, kind, competition = setup_subscription(db)
    cancelled = make_event(db, kind, competition=competition, start_time=SOON, title="A vs B")
    postponed = make_event(db, kind, competition=competition, start_time=SOON + timedelta(hours=3), title="C vs D")
    cancelled.status, postponed.status = EventStatus.CANCELLED, EventStatus.POSTPONED
    db.flush()

    first, second = feed(client, user.ical_token).walk("VEVENT")

    assert (str(first["SUMMARY"]), str(first["STATUS"])) == ("[Cancelled] A vs B", "CANCELLED")
    assert str(second["SUMMARY"]) == "[Postponed] C vs D"


def test_events_outside_the_window_are_left_out(client: TestClient, db: Session) -> None:
    user, kind, competition = setup_subscription(db)
    make_event(db, kind, competition=competition, start_time=datetime.now(UTC) - timedelta(days=60))

    assert feed(client, user.ical_token).walk("VEVENT") == []


def test_unknown_token_returns_404(client: TestClient) -> None:
    assert client.get("/calendar/not-a-real-token.ics").status_code == 404


def test_inactive_user_feed_returns_404(client: TestClient, db: Session) -> None:
    user = make_user(db)
    user.is_active = False
    db.flush()

    assert client.get(f"/calendar/{user.ical_token}.ics").status_code == 404


def test_feed_is_cached(client: TestClient, db: Session, cache: MemoryCache) -> None:
    user, kind, competition = setup_subscription(db)
    feed(client, user.ical_token)
    make_event(db, kind, competition=competition, start_time=SOON)  # arrives after caching

    assert feed(client, user.ical_token).walk("VEVENT") == []  # served from cache until the TTL expires
    assert f"ical:{user.ical_token}" in cache.data
