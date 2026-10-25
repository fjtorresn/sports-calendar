"""Providers against recorded (trimmed) real responses: no network in tests."""

import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

from app.ingestion.base import ProviderError
from app.ingestion.providers.football_data import FootballDataProvider, parse_matches
from app.ingestion.providers.jolpica import JolpicaProvider, parse_races
from app.models.enums import EventStatus, TimePrecision

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


# --- football-data.org ---------------------------------------------------------------


def test_football_data_maps_matches() -> None:
    events = {e.external_id: e for e in parse_matches(load("football_data_cl_matches.json"))}

    timed = events["575377"]
    assert timed.title == "Shaktar vs Sporting CP"
    assert timed.start_time == datetime(2026, 11, 3, 17, 45, tzinfo=UTC)
    assert (timed.status, timed.time_precision) == (EventStatus.SCHEDULED, TimePrecision.EXACT)
    home, away = timed.participants
    assert (home.competitor.name, home.is_home, away.is_home) == ("FK Shakhtar Donetsk", True, False)


def test_football_data_status_and_precision() -> None:
    events = {e.external_id: e for e in parse_matches(load("football_data_cl_matches.json"))}

    assert events["575323"].status == EventStatus.FINISHED
    assert events["900001"].time_precision == TimePrecision.DATE_ONLY  # SCHEDULED: date only
    assert events["900002"].status == EventStatus.POSTPONED


def test_football_data_skips_matches_with_undecided_teams() -> None:
    ids = {e.external_id for e in parse_matches(load("football_data_cl_matches.json"))}

    assert "900003" not in ids  # FR-5: only confirmed events
    assert len(ids) == 5


def _client(handler) -> httpx.Client:
    return httpx.Client(base_url="https://api.test", transport=httpx.MockTransport(handler))


def test_football_data_retries_after_429() -> None:
    responses = iter(
        [
            httpx.Response(429, headers={"X-RequestCounter-Reset": "7"}),
            httpx.Response(200, json=load("football_data_cl_matches.json")),
        ]
    )
    sleeps: list[float] = []
    provider = FootballDataProvider("key", client=_client(lambda _: next(responses)), sleep=sleeps.append)

    assert len(provider.fetch_events("CL")) == 5
    assert sleeps == [7.0]


def test_football_data_waits_when_the_minute_quota_is_used_up() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-Auth-Token"] == "key"
        headers = {"X-Requests-Available-Minute": "0", "X-RequestCounter-Reset": "30"}
        return httpx.Response(200, json={"matches": []}, headers=headers)

    sleeps: list[float] = []
    FootballDataProvider("key", client=_client(handler), sleep=sleeps.append).fetch_events("CL")

    assert sleeps == [30.0]


def test_football_data_errors_become_provider_errors() -> None:
    provider = FootballDataProvider("bad-key", client=_client(lambda _: httpx.Response(403, text="forbidden")))

    with pytest.raises(ProviderError, match="403"):
        provider.fetch_events("CL")


# --- Jolpica (F1) ----------------------------------------------------------------------


def test_jolpica_creates_one_event_per_session() -> None:
    events = parse_races(load("jolpica_races.json"))
    china = [e for e in events if e.title.startswith("Chinese Grand Prix")]
    vegas = [e for e in events if e.title.startswith("Las Vegas Grand Prix")]

    assert [e.event_kind for e in china] == ["practice", "sprint_qualifying", "sprint", "qualifying", "race"]
    assert [e.event_kind for e in vegas] == ["practice", "practice", "practice", "qualifying", "race"]
    assert len({e.external_id for e in events}) == len(events)


def test_jolpica_session_details() -> None:
    race = next(e for e in parse_races(load("jolpica_races.json")) if e.title == "Las Vegas Grand Prix – Race")

    assert race.start_time == datetime(2026, 11, 22, 4, 0, tzinfo=UTC)
    assert race.time_precision == TimePrecision.EXACT
    assert race.venue is not None and "Las Vegas" in race.venue
    assert race.participants == ()


def test_jolpica_fetch() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/current/races/")
        return httpx.Response(200, json=load("jolpica_races.json"))

    assert len(JolpicaProvider(client=_client(handler)).fetch_events("f1")) == 10
