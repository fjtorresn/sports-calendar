"""Catalog: what can be followed (sports, competitions, competitors) and how events are classified."""

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import CompetitorKind, string_enum


class Nation(Base):
    __tablename__ = "nations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    # Sports codes (ESP, ENG…) rather than ISO 3166: England and Scotland compete separately.
    code: Mapped[str] = mapped_column(String(3), unique=True)


class Sport(Base):
    __tablename__ = "sports"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(100))

    event_kinds: Mapped[list["EventKind"]] = relationship(back_populates="sport", order_by="EventKind.display_order")


class EventKind(Base):
    """A type of event within a sport (F1: practice, qualifying, race…; football: match)."""

    __tablename__ = "event_kinds"
    __table_args__ = (UniqueConstraint("sport_id", "slug"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    sport_id: Mapped[int] = mapped_column(ForeignKey("sports.id", ondelete="RESTRICT"))
    slug: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(100))
    # Preselected in the UI when subscribing; an empty selection still means "all kinds".
    is_default: Mapped[bool] = mapped_column(default=False, server_default="false")
    display_order: Mapped[int] = mapped_column(default=0, server_default="0")

    sport: Mapped[Sport] = relationship(back_populates="event_kinds")


class Competition(Base):
    __tablename__ = "competitions"
    __table_args__ = (UniqueConstraint("sport_id", "slug"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    sport_id: Mapped[int] = mapped_column(ForeignKey("sports.id", ondelete="RESTRICT"))
    slug: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(150))
    nation_id: Mapped[int | None] = mapped_column(ForeignKey("nations.id", ondelete="SET NULL"))

    sport: Mapped[Sport] = relationship()


class Competitor(Base):
    """Anyone who competes: a team (Barcelona, Red Bull) or an individual (Djokovic). See ADR 0003."""

    __tablename__ = "competitors"

    id: Mapped[int] = mapped_column(primary_key=True)
    sport_id: Mapped[int] = mapped_column(ForeignKey("sports.id", ondelete="RESTRICT"), index=True)
    kind: Mapped[CompetitorKind] = mapped_column(string_enum(CompetitorKind))
    name: Mapped[str] = mapped_column(String(150))
    short_name: Mapped[str | None] = mapped_column(String(50))
    nation_id: Mapped[int | None] = mapped_column(ForeignKey("nations.id", ondelete="SET NULL"), index=True)

    nation: Mapped[Nation | None] = relationship()
