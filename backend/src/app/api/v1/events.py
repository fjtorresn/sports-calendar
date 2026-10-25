from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.event import Event
from app.schemas.event import EventResponse

router = APIRouter()


@router.get("/", response_model=list[EventResponse])
def get_events(
    start_date: datetime | None = Query(None, description="Start of the range (ISO 8601, UTC)"),
    end_date: datetime | None = Query(None, description="End of the range (ISO 8601, UTC)"),
    db: Session = Depends(get_db),
):
    query = db.query(Event)

    if start_date:
        query = query.filter(Event.start_time >= start_date)
    if end_date:
        query = query.filter(Event.start_time <= end_date)

    query = query.order_by(Event.start_time.asc())

    return query.all()
