from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.event import Event
from app.schemas.event import EventResponse

router = APIRouter()


@router.get("/", response_model=list[EventResponse])
def get_events(
    # Filtros opcionales en la URL (Query Params)
    start_date: datetime | None = Query(None, description="Fecha inicio (ISO 8601 UTC)"),
    end_date: datetime | None = Query(None, description="Fecha fin (ISO 8601 UTC)"),
    db: Session = Depends(get_db),
):
    # Iniciamos la consulta base
    query = db.query(Event)

    # Aplicamos filtros dinámicamente si el usuario los envió
    if start_date:
        query = query.filter(Event.start_time >= start_date)
    if end_date:
        query = query.filter(Event.start_time <= end_date)

    # Ordenamos por fecha de inicio (los más próximos primero)
    query = query.order_by(Event.start_time.asc())

    # Ejecutamos la búsqueda en la BD
    events = query.all()

    return events
