"""Jolpica-F1 adapter (Ergast-compatible, open, 500 requests/hour)."""

from datetime import UTC, date, datetime, time
from typing import Any

import httpx

from app.ingestion.base import EventData, ProviderError
from app.models.enums import DataSource, TimePrecision

BASE_URL = "https://api.jolpi.ca/ergast/f1"

# Session key in the payload -> (our event kind slug, label in the title).
SESSIONS = [
    ("FirstPractice", "practice", "Practice 1"),
    ("SecondPractice", "practice", "Practice 2"),
    ("ThirdPractice", "practice", "Practice 3"),
    ("SprintQualifying", "sprint_qualifying", "Sprint Qualifying"),
    ("SprintShootout", "sprint_qualifying", "Sprint Shootout"),  # the 2023 name
    ("Sprint", "sprint", "Sprint"),
    ("Qualifying", "qualifying", "Qualifying"),
]


def _start(session: dict[str, Any]) -> tuple[datetime, TimePrecision]:
    day = date.fromisoformat(session["date"])
    if "time" not in session:
        return datetime.combine(day, time(), tzinfo=UTC), TimePrecision.DATE_ONLY
    return datetime.fromisoformat(f"{session['date']}T{session['time'].replace('Z', '+00:00')}"), TimePrecision.EXACT


def parse_races(payload: dict[str, Any]) -> list[EventData]:
    table = payload["MRData"]["RaceTable"]
    events = []
    for race in table["Races"]:
        prefix = f"{race['season']}-{race['round']}"
        circuit = race["Circuit"]
        venue = f"{circuit['circuitName']}, {circuit['Location']['locality']}"
        sessions = [(key, kind, label, race[key]) for key, kind, label in SESSIONS if key in race]
        sessions.append(("Race", "race", "Race", race))
        for key, kind, label, session in sessions:
            start, precision = _start(session)
            events.append(
                EventData(
                    external_id=f"{prefix}-{key}",
                    event_kind=kind,
                    title=f"{race['raceName']} – {label}",
                    start_time=start,
                    time_precision=precision,
                    venue=venue,
                )
            )
    return events


class JolpicaProvider:
    source = DataSource.JOLPICA

    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client(base_url=BASE_URL, timeout=20)

    def fetch_events(self, competition_external_id: str) -> list[EventData]:
        # The F1 championship is the only Jolpica competition; it is always the current season.
        try:
            response = self._client.get("/current/races/", params={"limit": 100})
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderError(f"Jolpica request failed: {exc}") from exc
        return parse_races(response.json())
