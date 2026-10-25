"""Which competitions get synced (on-demand ingestion, design.md §3.3)."""

from sqlalchemy.orm import Session

from app.ingestion.runner import followed_competition_ids
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


def test_nothing_is_followed_without_subscriptions(db: Session) -> None:
    make_competition(db, make_sport(db))

    assert followed_competition_ids(db) == set()


def test_direct_and_sport_subscriptions(db: Session) -> None:
    football, f1 = make_sport(db), make_sport(db)
    ucl, liga = make_competition(db, football), make_competition(db, football)
    championship = make_competition(db, f1)
    user = make_user(db)
    make_subscription(db, user, competition_id=ucl.id)
    make_subscription(db, user, sport_id=f1.id)

    assert followed_competition_ids(db) == {ucl.id, championship.id}
    assert liga.id not in followed_competition_ids(db)


def test_competitor_and_nation_subscriptions_follow_competitions_with_their_events(db: Session) -> None:
    football = make_sport(db)
    match = make_event_kind(db, football)
    italy = make_nation(db, "ITA")
    ucl, liga, serie_a = (make_competition(db, football) for _ in range(3))
    barcelona = make_competitor(db, football, "Barcelona")
    inter = make_competitor(db, football, "Inter", nation=italy)
    make_event(db, match, competition=liga, participants=(barcelona,))
    make_event(db, match, competition=serie_a, participants=(inter,))
    make_competition(db, football)  # never played by anyone followed
    user = make_user(db)
    make_subscription(db, user, competitor_id=barcelona.id)
    make_subscription(db, user, nation_id=italy.id)

    assert followed_competition_ids(db) == {liga.id, serie_a.id}
    assert ucl.id not in followed_competition_ids(db)
