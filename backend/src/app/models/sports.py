from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from .event import Event


class Nation(Base):
    __tablename__ = "nations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    iso_code: Mapped[str] = mapped_column(String(3), unique=True, nullable=False)
    flag_url: Mapped[str | None] = mapped_column(String(255))

    teams: Mapped[list["Team"]] = relationship(back_populates="nation")
    players: Mapped[list["Player"]] = relationship(back_populates="nation")


class Sport(Base):
    __tablename__ = "sports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    participant_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "team", "player", "mixed"

    competitions: Mapped[list["Competition"]] = relationship(back_populates="sport")


class Competition(Base):
    __tablename__ = "competitions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    sport_id: Mapped[int] = mapped_column(ForeignKey("sports.id", ondelete="CASCADE"))
    nation_id: Mapped[int | None] = mapped_column(ForeignKey("nations.id", ondelete="SET NULL"))

    sport: Mapped["Sport"] = relationship(back_populates="competitions")
    events: Mapped[list["Event"]] = relationship(back_populates="competition")


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    is_national_team: Mapped[bool] = mapped_column(default=False)
    sport_id: Mapped[int] = mapped_column(ForeignKey("sports.id", ondelete="CASCADE"))
    nation_id: Mapped[int] = mapped_column(ForeignKey("nations.id", ondelete="RESTRICT"))

    nation: Mapped["Nation"] = relationship(back_populates="teams")
    players: Mapped[list["Player"]] = relationship(back_populates="team")


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id", ondelete="SET NULL"))
    nation_id: Mapped[int] = mapped_column(ForeignKey("nations.id", ondelete="RESTRICT"))

    team: Mapped[Optional["Team"]] = relationship(back_populates="players")
    nation: Mapped["Nation"] = relationship(back_populates="players")
