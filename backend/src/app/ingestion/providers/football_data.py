"""football-data.org v4 adapter (free plan: 13 competitions, 10 requests/minute)."""

import logging
import time
from collections.abc import Callable
from datetime import datetime
from typing import Any

import httpx

from app.ingestion.base import CompetitorData, EventData, ParticipantData, ProviderError
from app.models.enums import DataSource, EventStatus, TimePrecision

logger = logging.getLogger(__name__)

BASE_URL = "https://api.football-data.org/v4"
MAX_RETRIES = 3

# football-data status -> (our status, how precise the kick-off time is).
# TIMED means date and time are confirmed; SCHEDULED means only the date is.
STATUS_MAP: dict[str, tuple[EventStatus, TimePrecision]] = {
    "SCHEDULED": (EventStatus.SCHEDULED, TimePrecision.DATE_ONLY),
    "TIMED": (EventStatus.SCHEDULED, TimePrecision.EXACT),
    "IN_PLAY": (EventStatus.SCHEDULED, TimePrecision.EXACT),
    "PAUSED": (EventStatus.SCHEDULED, TimePrecision.EXACT),
    "FINISHED": (EventStatus.FINISHED, TimePrecision.EXACT),
    "AWARDED": (EventStatus.FINISHED, TimePrecision.EXACT),
    "POSTPONED": (EventStatus.POSTPONED, TimePrecision.DATE_ONLY),
    "SUSPENDED": (EventStatus.POSTPONED, TimePrecision.EXACT),
    "CANCELLED": (EventStatus.CANCELLED, TimePrecision.EXACT),
}


def _team(data: dict[str, Any]) -> CompetitorData | None:
    if data.get("id") is None:
        return None
    return CompetitorData(external_id=str(data["id"]), name=data["name"], short_name=data.get("shortName"))


def parse_matches(payload: dict[str, Any]) -> list[EventData]:
    events = []
    for match in payload.get("matches", []):
        home, away = _team(match["homeTeam"]), _team(match["awayTeam"])
        if home is None or away is None:
            # Knockout ties not decided yet: only confirmed events are shown (FR-5).
            continue
        mapped = STATUS_MAP.get(match["status"])
        if mapped is None:
            logger.warning("Skipping match %s with unknown status %r", match["id"], match["status"])
            continue
        status, precision = mapped
        events.append(
            EventData(
                external_id=str(match["id"]),
                event_kind="match",
                title=f"{home.short_name or home.name} vs {away.short_name or away.name}",
                start_time=datetime.fromisoformat(match["utcDate"]),
                time_precision=precision,
                status=status,
                participants=(ParticipantData(home, is_home=True), ParticipantData(away, is_home=False)),
            )
        )
    return events


class FootballDataProvider:
    source = DataSource.FOOTBALL_DATA

    def __init__(
        self,
        api_key: str,
        client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._client = client or httpx.Client(base_url=BASE_URL, timeout=20)
        self._headers = {"X-Auth-Token": api_key}
        self._sleep = sleep

    def fetch_events(self, competition_external_id: str) -> list[EventData]:
        return parse_matches(self._get(f"/competitions/{competition_external_id}/matches"))

    def _get(self, path: str) -> dict[str, Any]:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self._client.get(path, headers=self._headers)
            except httpx.HTTPError as exc:
                raise ProviderError(f"football-data request failed: {exc}") from exc

            if response.status_code == 429 and attempt < MAX_RETRIES:
                wait = float(response.headers.get("X-RequestCounter-Reset", 60))
                logger.info("football-data quota reached, waiting %.0fs (attempt %d)", wait, attempt)
                self._sleep(wait)
                continue
            if response.is_error:
                raise ProviderError(f"football-data {path} returned {response.status_code}: {response.text[:200]}")

            # Stay under the per-minute quota instead of hitting 429s.
            if response.headers.get("X-Requests-Available-Minute") == "0":
                self._sleep(float(response.headers.get("X-RequestCounter-Reset", 60)))
            return response.json()
        raise ProviderError(f"football-data {path}: quota still exhausted after {MAX_RETRIES} attempts")
