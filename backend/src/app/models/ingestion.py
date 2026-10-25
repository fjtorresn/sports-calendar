"""Bookkeeping for data ingestion: identity across sources and sync progress (design.md §4.5, §5.2)."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin
from app.models.enums import DataSource, SyncStatus, string_enum


class ExternalRefMixin:
    """How a source identifies one of our entities.

    UNIQUE (source, external_id) is what makes the ingestion upsert idempotent.
    """

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[DataSource] = mapped_column(string_enum(DataSource))
    external_id: Mapped[str] = mapped_column(String(100))


class CompetitionExternalRef(ExternalRefMixin, Base):
    __tablename__ = "competition_external_refs"
    __table_args__ = (UniqueConstraint("source", "external_id"), UniqueConstraint("competition_id", "source"))

    competition_id: Mapped[int] = mapped_column(ForeignKey("competitions.id", ondelete="CASCADE"))


class CompetitorExternalRef(ExternalRefMixin, Base):
    __tablename__ = "competitor_external_refs"
    __table_args__ = (UniqueConstraint("source", "external_id"), UniqueConstraint("competitor_id", "source"))

    competitor_id: Mapped[int] = mapped_column(ForeignKey("competitors.id", ondelete="CASCADE"))


class EventExternalRef(ExternalRefMixin, Base):
    __tablename__ = "event_external_refs"
    __table_args__ = (UniqueConstraint("source", "external_id"), UniqueConstraint("event_id", "source"))

    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"))


class SyncState(TimestampMixin, Base):
    """When a competition was last synced from a source, and how it went."""

    __tablename__ = "sync_state"
    __table_args__ = (UniqueConstraint("competition_id", "source"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    competition_id: Mapped[int] = mapped_column(ForeignKey("competitions.id", ondelete="CASCADE"))
    source: Mapped[DataSource] = mapped_column(string_enum(DataSource))
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_status: Mapped[SyncStatus | None] = mapped_column(string_enum(SyncStatus))
    last_error: Mapped[str | None] = mapped_column(Text)
