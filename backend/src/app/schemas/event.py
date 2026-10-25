from datetime import datetime

from app.models.enums import EventStatus, TimePrecision
from app.schemas.catalog import CompetitionResponse, CompetitorResponse, EventKindResponse, ORMModel


class EventParticipantResponse(ORMModel):
    competitor: CompetitorResponse
    is_home: bool | None


class EventResponse(ORMModel):
    id: int
    sport_id: int
    title: str
    start_time: datetime
    time_precision: TimePrecision
    status: EventStatus
    venue: str | None
    competition: CompetitionResponse | None
    event_kind: EventKindResponse
    # Nested so clients get the whole event in a single response.
    participants: list[EventParticipantResponse]
