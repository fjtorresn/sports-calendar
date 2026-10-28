"""The private iCal feed (FR-7, ADR 0004). Kept outside /api/v1: subscribed URLs must never change."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.cache import Cache, get_cache
from app.core.database import get_db
from app.models import User
from app.services.calendar import get_calendar_events
from app.services.ical import render_calendar

router = APIRouter(tags=["Calendar"])

PAST_WINDOW = timedelta(days=30)
FUTURE_WINDOW = timedelta(days=365)
CACHE_TTL_SECONDS = 60 * 60


def cache_key(token: str) -> str:
    return f"ical:{token}"


@router.get("/calendar/{token}.ics", response_class=Response)
def calendar_feed(token: str, db: Session = Depends(get_db), cache: Cache = Depends(get_cache)) -> Response:
    # The token is the credential: never echo it back in errors or logs.
    user = db.scalar(select(User).where(User.ical_token == token, User.is_active))
    if user is None:
        raise HTTPException(status_code=404, detail="Calendar not found")

    body = cache.get(cache_key(token))
    if body is None:
        now = datetime.now(UTC)
        events = get_calendar_events(db, user.id, now - PAST_WINDOW, now + FUTURE_WINDOW)
        body = render_calendar(events)
        cache.set(cache_key(token), body, CACHE_TTL_SECONDS)

    return Response(
        content=body,
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": 'inline; filename="sports-calendar.ics"'},
    )
