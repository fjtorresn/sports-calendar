from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


# ==========================================
# EVENT PARTICIPANT SCHEMAS
# ==========================================
class EventParticipantBase(BaseModel):
    participant_type: str
    participant_id: int
    is_home: bool | None = True


class EventParticipantResponse(EventParticipantBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# EVENT SCHEMAS
# ==========================================
class EventBase(BaseModel):
    sport_id: int
    competition_id: int | None = None
    start_time: datetime
    status: str
    result_details: dict[str, Any] | None = None


class EventResponse(EventBase):
    id: int
    created_by_user_id: int | None = None

    # Anidamos los participantes para que el frontend reciba todo en un solo JSON
    participants: list[EventParticipantResponse] = []

    model_config = ConfigDict(from_attributes=True)
