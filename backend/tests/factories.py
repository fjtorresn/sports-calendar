"""Small helpers to build test data. Each one flushes so the new row has an id."""

from datetime import UTC, datetime
from itertools import count

from sqlalchemy.orm import Session

from app.models import Competition, Competitor, Event, EventKind, EventParticipant, Nation, Sport, Subscription, User
from app.models.enums import CompetitorKind

_seq = count(1)


def _flush[T](db: Session, obj: T) -> T:
    db.add(obj)
    db.flush()
    return obj


def make_nation(db: Session, code: str | None = None) -> Nation:
    n = next(_seq)
    return _flush(db, Nation(name=f"Nation {n}", code=code or f"N{n:02d}"[:3]))


def make_sport(db: Session, slug: str | None = None) -> Sport:
    n = next(_seq)
    return _flush(db, Sport(slug=slug or f"sport-{n}", name=f"Sport {n}"))


def make_event_kind(db: Session, sport: Sport, slug: str = "match", *, is_default: bool = True) -> EventKind:
    return _flush(db, EventKind(sport_id=sport.id, slug=slug, name=slug.title(), is_default=is_default))


def make_competition(db: Session, sport: Sport, name: str | None = None) -> Competition:
    n = next(_seq)
    return _flush(db, Competition(sport_id=sport.id, slug=f"competition-{n}", name=name or f"Competition {n}"))


def make_competitor(db: Session, sport: Sport, name: str | None = None, *, nation: Nation | None = None) -> Competitor:
    n = next(_seq)
    return _flush(
        db,
        Competitor(
            sport_id=sport.id,
            kind=CompetitorKind.TEAM,
            name=name or f"Competitor {n}",
            nation_id=nation.id if nation else None,
        ),
    )


def make_event(
    db: Session,
    kind: EventKind,
    *,
    competition: Competition | None = None,
    participants: tuple[Competitor, ...] = (),
    start_time: datetime | None = None,
    title: str | None = None,
) -> Event:
    event = Event(
        sport_id=kind.sport_id,
        event_kind_id=kind.id,
        competition_id=competition.id if competition else None,
        title=title or f"Event {next(_seq)}",
        start_time=start_time or datetime(2026, 11, 1, 20, 0, tzinfo=UTC),
        participants=[EventParticipant(competitor_id=c.id) for c in participants],
    )
    return _flush(db, event)


def make_user(db: Session) -> User:
    n = next(_seq)
    return _flush(db, User(email=f"user{n}@example.com", hashed_password="not-a-real-hash"))


def make_subscription(
    db: Session, user: User, *, event_kinds: tuple[EventKind, ...] = (), **filters: int
) -> Subscription:
    """``filters`` are column values, e.g. ``competitor_id=barcelona.id``."""
    return _flush(db, Subscription(user_id=user.id, event_kinds=list(event_kinds), **filters))
