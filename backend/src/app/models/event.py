from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.app.core.database import Base

if TYPE_CHECKING:
    from .sports import Sport, Competition
    from .user import User
class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Llave foránea directa al deporte (Obligatoria para todo evento)
    sport_id: Mapped[int] = mapped_column(ForeignKey("sports.id", ondelete="CASCADE"), index=True)
    
    # Opcional, ya que los eventos de usuarios no tendrán competición
    competition_id: Mapped[Optional[int]] = mapped_column(ForeignKey("competitions.id", ondelete="CASCADE"), nullable=True)
    
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="scheduled")
    result_details: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_by_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relaciones
    sport: Mapped["Sport"] = relationship()
    competition: Mapped[Optional["Competition"]] = relationship(back_populates="events")
    creator: Mapped[Optional["User"]] = relationship(back_populates="own_events")
    participants: Mapped[List["EventParticipant"]] = relationship(back_populates="event", cascade="all, delete-orphan")


class EventParticipant(Base):
    __tablename__ = "event_participants"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    
    participant_type: Mapped[str] = mapped_column(String(20), nullable=False) # "team", "player", "user"
    participant_id: Mapped[int] = mapped_column(nullable=False)
    is_home: Mapped[Optional[bool]] = mapped_column(default=True)

    event: Mapped["Event"] = relationship(back_populates="participants")