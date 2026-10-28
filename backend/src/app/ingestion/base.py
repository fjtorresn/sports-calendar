"""The contract between data sources and the rest of the system (ADR 0002).

Providers translate a source's format into these DTOs; ``sync.py`` turns DTOs into rows.
Nothing outside ``app.ingestion.providers`` knows what any source's API looks like.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

from app.models.enums import CompetitorKind, DataSource, EventStatus, TimePrecision


class ProviderError(Exception):
    """A source could not be read (network, auth, quota, unexpected payload)."""


@dataclass(frozen=True)
class CompetitorData:
    external_id: str
    name: str
    short_name: str | None = None
    kind: CompetitorKind = CompetitorKind.TEAM


@dataclass(frozen=True)
class ParticipantData:
    competitor: CompetitorData
    is_home: bool | None = None


@dataclass(frozen=True)
class EventData:
    external_id: str
    event_kind: str  # an EventKind slug of the competition's sport, e.g. "match" or "race"
    title: str
    start_time: datetime
    time_precision: TimePrecision
    status: EventStatus = EventStatus.SCHEDULED
    venue: str | None = None
    participants: tuple[ParticipantData, ...] = field(default_factory=tuple)


class EventProvider(Protocol):
    source: DataSource

    def fetch_events(self, competition_external_id: str) -> list[EventData]:
        """Every confirmed event of the competition's current season."""
        ...
