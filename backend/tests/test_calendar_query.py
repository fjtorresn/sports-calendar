"""Subscription semantics (design.md §4.3): AND within a subscription, OR across them."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.models import Event, EventKind, User
from app.services.calendar import get_calendar_events
from tests.factories import (
    make_competition,
    make_competitor,
    make_event,
    make_event_kind,
    make_nation,
    make_sport,
    make_subscription,
    make_user,
)

START = datetime(2026, 11, 1, tzinfo=UTC)
END = datetime(2026, 12, 1, tzinfo=UTC)


@dataclass
class World:
    """A small catalog with known events, built fresh (and rolled back) for each test."""

    user: User
    football_id: int
    f1_id: int
    barcelona_id: int
    italy_id: int
    champions_league_id: int
    la_liga_id: int
    f1_championship_id: int
    race: EventKind
    qualifying: EventKind
    barca_inter_ucl: Event
    barca_madrid_liga: Event
    madrid_inter_ucl: Event
    f1_practice: Event
    f1_qualifying: Event
    f1_race: Event


@pytest.fixture
def world(db: Session) -> World:
    spain, italy = make_nation(db, "ESP"), make_nation(db, "ITA")

    football = make_sport(db, "football")
    match = make_event_kind(db, football, "match")
    ucl, la_liga = make_competition(db, football, "Champions League"), make_competition(db, football, "LaLiga")
    barcelona = make_competitor(db, football, "Barcelona", nation=spain)
    madrid = make_competitor(db, football, "Real Madrid", nation=spain)
    inter = make_competitor(db, football, "Inter", nation=italy)

    f1 = make_sport(db, "formula-1")
    practice = make_event_kind(db, f1, "practice", is_default=False)
    qualifying, race = make_event_kind(db, f1, "qualifying"), make_event_kind(db, f1, "race")
    championship = make_competition(db, f1, "F1 World Championship")

    day = timedelta(days=1)
    return World(
        user=make_user(db),
        football_id=football.id,
        f1_id=f1.id,
        barcelona_id=barcelona.id,
        italy_id=italy.id,
        champions_league_id=ucl.id,
        la_liga_id=la_liga.id,
        f1_championship_id=championship.id,
        race=race,
        qualifying=qualifying,
        barca_inter_ucl=make_event(db, match, competition=ucl, participants=(barcelona, inter), start_time=START),
        barca_madrid_liga=make_event(
            db, match, competition=la_liga, participants=(barcelona, madrid), start_time=START + day
        ),
        madrid_inter_ucl=make_event(
            db, match, competition=ucl, participants=(madrid, inter), start_time=START + 2 * day
        ),
        f1_practice=make_event(db, practice, competition=championship, start_time=START + 3 * day),
        f1_qualifying=make_event(db, qualifying, competition=championship, start_time=START + 4 * day),
        f1_race=make_event(db, race, competition=championship, start_time=START + 5 * day),
    )


def calendar(db: Session, user: User, start: datetime = START, end: datetime = END) -> list[Event]:
    return get_calendar_events(db, user.id, start, end)


def test_user_without_subscriptions_gets_an_empty_calendar(db: Session, world: World) -> None:
    assert calendar(db, world.user) == []


def test_filters_within_a_subscription_are_combined_with_and(db: Session, world: World) -> None:
    make_subscription(db, world.user, competitor_id=world.barcelona_id, competition_id=world.champions_league_id)

    assert calendar(db, world.user) == [world.barca_inter_ucl]


def test_subscriptions_are_combined_with_or(db: Session, world: World) -> None:
    make_subscription(db, world.user, competitor_id=world.barcelona_id, competition_id=world.champions_league_id)
    make_subscription(db, world.user, competition_id=world.la_liga_id)

    assert calendar(db, world.user) == [world.barca_inter_ucl, world.barca_madrid_liga]


def test_event_matched_by_several_subscriptions_appears_once(db: Session, world: World) -> None:
    make_subscription(db, world.user, competitor_id=world.barcelona_id)
    make_subscription(db, world.user, competition_id=world.champions_league_id)

    assert calendar(db, world.user) == [world.barca_inter_ucl, world.barca_madrid_liga, world.madrid_inter_ucl]


def test_sport_subscription_includes_every_event_of_the_sport(db: Session, world: World) -> None:
    make_subscription(db, world.user, sport_id=world.f1_id)

    assert calendar(db, world.user) == [world.f1_practice, world.f1_qualifying, world.f1_race]


def test_event_kind_filter_keeps_only_selected_kinds(db: Session, world: World) -> None:
    make_subscription(
        db, world.user, competition_id=world.f1_championship_id, event_kinds=(world.qualifying, world.race)
    )

    assert calendar(db, world.user) == [world.f1_qualifying, world.f1_race]


def test_nation_subscription_matches_events_with_a_competitor_from_that_nation(db: Session, world: World) -> None:
    make_subscription(db, world.user, nation_id=world.italy_id)

    assert calendar(db, world.user) == [world.barca_inter_ucl, world.madrid_inter_ucl]


def test_date_range_is_half_open(db: Session, world: World) -> None:
    make_subscription(db, world.user, sport_id=world.football_id)
    end = world.barca_madrid_liga.start_time  # excluded: the range is [start, end)

    assert calendar(db, world.user, end=end) == [world.barca_inter_ucl]


def test_other_users_subscriptions_do_not_leak(db: Session, world: World) -> None:
    other = make_user(db)
    make_subscription(db, other, sport_id=world.football_id)

    assert calendar(db, world.user) == []
