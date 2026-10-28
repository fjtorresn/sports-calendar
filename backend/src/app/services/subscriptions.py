"""Users and subscriptions. Used by the CLI now and by the API in phase 4."""

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Competition, Competitor, EventKind, Sport, Subscription, User
from app.models.user import generate_ical_token


class NotFoundError(ValueError):
    pass


class AmbiguousError(ValueError):
    pass


def ical_url(user: User) -> str:
    return f"{get_settings().public_base_url.rstrip('/')}/calendar/{user.ical_token}.ics"


def create_user(db: Session, email: str, timezone: str = "UTC") -> User:
    try:
        ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError(f"Unknown time zone {timezone!r} (use an IANA name like 'America/Santiago')") from exc
    if get_user(db, email, missing_ok=True):
        raise ValueError(f"A user with email {email!r} already exists")
    user = User(email=email.lower(), timezone=timezone)
    db.add(user)
    db.flush()
    return user


def get_user(db: Session, email: str, *, missing_ok: bool = False) -> User | None:
    user = db.scalar(select(User).where(User.email == email.lower()))
    if user is None and not missing_ok:
        raise NotFoundError(f"No user with email {email!r}")
    return user


def rotate_ical_token(db: Session, user: User) -> str:
    """Revokes the old feed URL immediately (ADR 0004)."""
    user.ical_token = generate_ical_token()
    db.flush()
    return ical_url(user)


def find_competitor(db: Session, name: str, sport_id: int | None = None) -> Competitor:
    """Exact (case-insensitive) name match first, then partial match; must resolve to one."""
    query = select(Competitor).order_by(Competitor.name)
    if sport_id is not None:
        query = query.where(Competitor.sport_id == sport_id)
    exact = list(db.scalars(query.where(func.lower(Competitor.name) == name.lower())))
    candidates = exact or list(
        db.scalars(
            query.where(Competitor.name.ilike(f"%{name}%") | Competitor.short_name.ilike(f"%{name}%")).limit(10)
        )
    )
    if not candidates:
        raise NotFoundError(f"No competitor matches {name!r}. Has its competition been synced?")
    if len(candidates) > 1:
        names = ", ".join(c.name for c in candidates)
        raise AmbiguousError(f"{name!r} matches several competitors: {names}")
    return candidates[0]


def _find_by_slug(db: Session, model: type[Sport] | type[Competition], slug: str, sport_id: int | None = None):
    query = select(model).where(model.slug == slug)
    if model is Competition and sport_id is not None:
        query = query.where(Competition.sport_id == sport_id)
    rows = list(db.scalars(query))
    if not rows:
        raise NotFoundError(f"No {model.__tablename__[:-1]} with slug {slug!r}")
    if len(rows) > 1:
        raise AmbiguousError(f"Several competitions use slug {slug!r}; pass --sport too")
    return rows[0]


def follow(
    db: Session,
    user: User,
    *,
    sport: str | None = None,
    competition: str | None = None,
    competitor: str | None = None,
    kinds: list[str] | None = None,
) -> Subscription:
    """Create a subscription; every given filter must match (AND). Slugs/names are resolved here."""
    if not (sport or competition or competitor):
        raise ValueError("A subscription needs at least one of sport, competition or competitor")

    sport_row = _find_by_slug(db, Sport, sport) if sport else None
    sport_id = sport_row.id if sport_row else None
    competition_row = _find_by_slug(db, Competition, competition, sport_id) if competition else None
    sport_id = sport_id or (competition_row.sport_id if competition_row else None)
    competitor_row = find_competitor(db, competitor, sport_id) if competitor else None
    sport_id = sport_id or (competitor_row.sport_id if competitor_row else None)

    selected_kinds = []
    for slug in kinds or []:
        kind = db.scalar(select(EventKind).where(EventKind.sport_id == sport_id, EventKind.slug == slug))
        if kind is None:
            valid = db.scalars(select(EventKind.slug).where(EventKind.sport_id == sport_id))
            raise NotFoundError(f"Unknown event kind {slug!r}; valid kinds: {', '.join(valid)}")
        selected_kinds.append(kind)

    subscription = Subscription(
        user_id=user.id,
        sport_id=sport_row.id if sport_row else None,
        competition_id=competition_row.id if competition_row else None,
        competitor_id=competitor_row.id if competitor_row else None,
        event_kinds=selected_kinds,
    )
    db.add(subscription)
    db.flush()
    return subscription


def describe(db: Session, subscription: Subscription) -> str:
    parts = []
    if subscription.sport_id:
        parts.append(f"sport={db.get(Sport, subscription.sport_id).slug}")
    if subscription.competition_id:
        parts.append(f"competition={db.get(Competition, subscription.competition_id).slug}")
    if subscription.competitor_id:
        parts.append(f"competitor={db.get(Competitor, subscription.competitor_id).name}")
    kinds = ",".join(k.slug for k in subscription.event_kinds) or "all"
    return f"#{subscription.id}: {' AND '.join(parts)} (kinds: {kinds})"
