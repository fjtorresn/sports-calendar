import pytest
from sqlalchemy.orm import Session

from app.scripts.seed import seed
from app.services import subscriptions as svc
from tests.factories import make_competitor


@pytest.fixture
def seeded(db: Session) -> Session:
    seed(db)
    return db


def test_create_user_validates_the_time_zone(db: Session) -> None:
    with pytest.raises(ValueError, match="Unknown time zone"):
        svc.create_user(db, "me@example.com", "Mars/Olympus")


def test_create_user_rejects_duplicate_emails(db: Session) -> None:
    svc.create_user(db, "Me@Example.com")

    with pytest.raises(ValueError, match="already exists"):
        svc.create_user(db, "me@example.com")


def test_ical_url_contains_the_token(db: Session) -> None:
    user = svc.create_user(db, "me@example.com")

    assert svc.ical_url(user).endswith(f"/calendar/{user.ical_token}.ics")


def test_rotating_the_token_changes_the_url(db: Session) -> None:
    user = svc.create_user(db, "me@example.com")
    old = svc.ical_url(user)

    assert svc.rotate_ical_token(db, user) != old


def test_follow_competitor_in_competition(seeded: Session) -> None:
    user = svc.create_user(seeded, "me@example.com")
    football = svc._find_by_slug(seeded, svc.Sport, "football")
    make_competitor(seeded, football, "FC Barcelona")

    subscription = svc.follow(seeded, user, competitor="barcelona", competition="champions-league")

    assert svc.describe(seeded, subscription).endswith(
        "competition=champions-league AND competitor=FC Barcelona (kinds: all)"
    )


def test_follow_f1_with_selected_kinds(seeded: Session) -> None:
    user = svc.create_user(seeded, "me@example.com")

    subscription = svc.follow(seeded, user, sport="formula-1", kinds=["qualifying", "race"])

    assert [k.slug for k in subscription.event_kinds] == ["qualifying", "race"]


def test_unknown_kind_lists_the_valid_ones(seeded: Session) -> None:
    user = svc.create_user(seeded, "me@example.com")

    with pytest.raises(svc.NotFoundError, match="valid kinds: .*race"):
        svc.follow(seeded, user, sport="formula-1", kinds=["warmup"])


def test_ambiguous_competitor_lists_candidates(seeded: Session) -> None:
    user = svc.create_user(seeded, "me@example.com")
    football = svc._find_by_slug(seeded, svc.Sport, "football")
    make_competitor(seeded, football, "Real Madrid CF")
    make_competitor(seeded, football, "Real Sociedad")

    with pytest.raises(svc.AmbiguousError, match="Real Madrid CF, Real Sociedad"):
        svc.follow(seeded, user, competitor="real")


def test_follow_needs_a_filter(db: Session) -> None:
    user = svc.create_user(db, "me@example.com")

    with pytest.raises(ValueError, match="at least one"):
        svc.follow(db, user, kinds=["race"])
