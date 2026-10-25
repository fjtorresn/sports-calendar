"""Render events as an iCalendar feed (RFC 5545) for Google / Apple / Outlook (ADR 0004)."""

from datetime import timedelta

from icalendar import Calendar
from icalendar import Event as ICalEvent

from app.models import Event
from app.models.enums import EventStatus, TimePrecision

# Sources give start times only; a typical duration makes the calendar block look right.
DURATIONS = {
    "match": timedelta(hours=2),
    "race": timedelta(hours=2),
    "practice": timedelta(hours=1),
    "qualifying": timedelta(hours=1),
    "sprint_qualifying": timedelta(minutes=45),
    "sprint": timedelta(hours=1),
}
DEFAULT_DURATION = timedelta(hours=2)

# How often clients should re-fetch the feed (a hint; Google applies its own schedule).
REFRESH_INTERVAL = timedelta(hours=6)


def event_uid(event: Event) -> str:
    """Stable across syncs, so a rescheduled event moves instead of being duplicated."""
    return f"event-{event.id}@sports-calendar"


def _summary(event: Event) -> str:
    match event.status:
        case EventStatus.POSTPONED:
            return f"[Postponed] {event.title}"
        case EventStatus.CANCELLED:
            return f"[Cancelled] {event.title}"
    if event.time_precision == TimePrecision.NOT_BEFORE:
        return f"{event.title} (not before {event.start_time:%H:%M} UTC)"
    return event.title


def _description(event: Event) -> str:
    lines = [event.competition.name] if event.competition else []
    if event.time_precision == TimePrecision.DATE_ONLY:
        lines.append("Kick-off time not confirmed yet.")
    return "\n".join(lines)


def render_calendar(events: list[Event], name: str = "Sports Calendar") -> bytes:
    calendar = Calendar()
    calendar.add("prodid", "-//Sports Calendar//EN")
    calendar.add("version", "2.0")
    calendar.add("calscale", "GREGORIAN")
    calendar.add("x-wr-calname", name)
    calendar.add("refresh-interval", REFRESH_INTERVAL, parameters={"VALUE": "DURATION"})
    calendar.add("x-published-ttl", REFRESH_INTERVAL)  # Apple / Outlook equivalent

    for event in events:
        item = ICalEvent()
        item.add("uid", event_uid(event))
        item.add("dtstamp", event.updated_at)
        item.add("last-modified", event.updated_at)
        item.add("summary", _summary(event))
        if event.time_precision == TimePrecision.DATE_ONLY:
            # All-day event: DTSTART;VALUE=DATE, with an exclusive end date.
            day = event.start_time.date()
            item.add("dtstart", day)
            item.add("dtend", day + timedelta(days=1))
        else:
            item.add("dtstart", event.start_time)
            item.add("dtend", event.start_time + DURATIONS.get(event.event_kind.slug, DEFAULT_DURATION))
        if description := _description(event):
            item.add("description", description)
        if event.venue:
            item.add("location", event.venue)
        if event.status == EventStatus.CANCELLED:
            item.add("status", "CANCELLED")
        calendar.add_component(item)
    return calendar.to_ical()
