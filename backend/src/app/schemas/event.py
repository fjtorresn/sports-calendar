from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict

# ==========================================
# EVENT PARTICIPANT SCHEMAS
# ==========================================
class EventParticipantBase(BaseModel):
    participant_type: str
    participant_id: int
    is_home: Optional[bool] = True

class EventParticipantResponse(EventParticipantBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

# ==========================================
# EVENT SCHEMAS
# ==========================================
class EventBase(BaseModel):
    sport_id: int
    competition_id: Optional[int] = None
    start_time: datetime
    status: str
    result_details: Optional[Dict[str, Any]] = None

class EventResponse(EventBase):
    id: int
    created_by_user_id: Optional[int] = None
    
    # Anidamos los participantes para que el frontend reciba todo en un solo JSON
    participants: List[EventParticipantResponse] = []
    
    model_config = ConfigDict(from_attributes=True)