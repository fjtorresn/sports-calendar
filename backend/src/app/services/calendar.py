"""The core calendar query (design.md §4.4): every event matching any of a user's subscriptions."""

from datetime import datetime

from sqlalchemy import exists, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import Competitor, Event, EventParticipant, Subscription, subscription_event_kinds


def _matching_subscription(user_id: int):
    """EXISTS a subscription of this user whose filters all match the outer event.

    Within a subscription every filter must match (AND); a NULL filter matches anything.
    The EXISTS itself provides the OR across subscriptions, and since it is a semi-join,
    an event matched by several subscriptions is still returned once (no DISTINCT needed).

    The inner subqueries reference tables two levels up (``events``), so they are correlated
    explicitly: auto-correlation only looks one level up, and would silently re-add ``events``
    to their FROM, making e.g. "Barcelona takes part" true for every event.
    """
    outer = (Event, Subscription)
    competitor_takes_part = (
        exists()
        .where(
            EventParticipant.event_id == Event.id,
            EventParticipant.competitor_id == Subscription.competitor_id,
        )
        .correlate(*outer)
    )
    nation_takes_part = (
        exists()
        .where(
            EventParticipant.event_id == Event.id,
            EventParticipant.competitor_id == Competitor.id,
            Competitor.nation_id == Subscription.nation_id,
        )
        .correlate(*outer)
    )
    has_kind_filter = exists().where(subscription_event_kinds.c.subscription_id == Subscription.id).correlate(*outer)
    kind_selected = (
        exists()
        .where(
            subscription_event_kinds.c.subscription_id == Subscription.id,
            subscription_event_kinds.c.event_kind_id == Event.event_kind_id,
        )
        .correlate(*outer)
    )
    return exists().where(
        Subscription.user_id == user_id,
        or_(Subscription.sport_id.is_(None), Subscription.sport_id == Event.sport_id),
        or_(Subscription.competition_id.is_(None), Subscription.competition_id == Event.competition_id),
        or_(Subscription.competitor_id.is_(None), competitor_takes_part),
        or_(Subscription.nation_id.is_(None), nation_takes_part),
        # No kinds selected means every kind of the sport (design.md §4.3).
        or_(~has_kind_filter, kind_selected),
    )


def get_calendar_events(db: Session, user_id: int, start: datetime, end: datetime) -> list[Event]:
    """Events in ``[start, end)`` matching at least one of the user's subscriptions (FR-3).

    The range is half-open so consecutive windows (this week, next week) never overlap.
    Related rows are loaded with ``selectinload``: one extra query per relationship
    instead of one per event (the N+1 problem).
    """
    query = (
        select(Event)
        .where(Event.start_time >= start, Event.start_time < end, _matching_subscription(user_id))
        .options(
            selectinload(Event.competition),
            selectinload(Event.event_kind),
            selectinload(Event.participants).selectinload(EventParticipant.competitor),
        )
        .order_by(Event.start_time, Event.id)
    )
    return list(db.scalars(query))
