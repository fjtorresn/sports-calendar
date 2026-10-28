from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.catalog import Competition, Competitor, EventKind
from app.models.enums import EventStatus, TimePrecision, string_enum


class Event(TimestampMixin, Base):
    __tablename__ = "events"
    __table_args__ = (
        # The core calendar query filters by competition or sport within a date range.
        Index("ix_events_competition_id_start_time", "competition_id", "start_time"),
        Index("ix_events_sport_id_start_time", "sport_id", "start_time"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sport_id: Mapped[int] = mapped_column(ForeignKey("sports.id", ondelete="RESTRICT"))
    competition_id: Mapped[int | None] = mapped_column(ForeignKey("competitions.id", ondelete="RESTRICT"))
    event_kind_id: Mapped[int] = mapped_column(ForeignKey("event_kinds.id", ondelete="RESTRICT"))
    # Groups related events, e.g. the sessions of a Grand Prix under the GP itself.
    parent_event_id: Mapped[int | None] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    time_precision: Mapped[TimePrecision] = mapped_column(
        string_enum(TimePrecision), default=TimePrecision.EXACT, server_default=TimePrecision.EXACT.value
    )
    status: Mapped[EventStatus] = mapped_column(
        string_enum(EventStatus), default=EventStatus.SCHEDULED, server_default=EventStatus.SCHEDULED.value
    )
    venue: Mapped[str | None] = mapped_column(String(200))

    competition: Mapped[Competition | None] = relationship()
    event_kind: Mapped[EventKind] = relationship()
    participants: Mapped[list["EventParticipant"]] = relationship(back_populates="event", cascade="all, delete-orphan")


class EventParticipant(Base):
    __tablename__ = "event_participants"
    __table_args__ = (
        # "Events where this competitor takes part" — the competitor filter of the core query.
        Index("ix_event_participants_competitor_id_event_id", "competitor_id", "event_id"),
    )

    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), primary_key=True)
    competitor_id: Mapped[int] = mapped_column(ForeignKey("competitors.id", ondelete="RESTRICT"), primary_key=True)
    # Only meaningful for home/away sports; NULL elsewhere (e.g. an F1 driver).
    is_home: Mapped[bool | None]

    event: Mapped[Event] = relationship(back_populates="participants")
    competitor: Mapped[Competitor] = relationship()
