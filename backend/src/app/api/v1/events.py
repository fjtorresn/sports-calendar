from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models import Event, EventParticipant
from app.schemas.event import EventResponse

router = APIRouter()


@router.get("/", response_model=list[EventResponse])
def list_events(
    start: datetime | None = Query(None, description="Start of the range (ISO 8601, UTC)"),
    end: datetime | None = Query(None, description="End of the range (ISO 8601, UTC)"),
    db: Session = Depends(get_db),
) -> list[Event]:
    query = (
        select(Event)
        .options(
            selectinload(Event.competition),
            selectinload(Event.event_kind),
            selectinload(Event.participants).selectinload(EventParticipant.competitor),
        )
        .order_by(Event.start_time)
    )
    if start:
        query = query.where(Event.start_time >= start)
    if end:
        query = query.where(Event.start_time <= end)
    return list(db.scalars(query))
