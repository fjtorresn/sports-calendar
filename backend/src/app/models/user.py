from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from .event import Event


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relaciones
    own_events: Mapped[list["Event"]] = relationship(back_populates="creator")
    subscriptions: Mapped[list["UserSubscription"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    # Columnas condicionales (Matriz de filtros)
    sport_id: Mapped[int | None] = mapped_column(ForeignKey("sports.id", ondelete="CASCADE"), nullable=True)
    competition_id: Mapped[int | None] = mapped_column(
        ForeignKey("competitions.id", ondelete="CASCADE"), nullable=True
    )
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), nullable=True)
    player_id: Mapped[int | None] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=True)
    nation_id: Mapped[int | None] = mapped_column(ForeignKey("nations.id", ondelete="CASCADE"), nullable=True)

    # Relaciones
    user: Mapped["User"] = relationship(back_populates="subscriptions")

    # Enforced by the database, not just the API: a subscription needs at least one filter.
    __table_args__ = (
        CheckConstraint(
            "sport_id IS NOT NULL OR competition_id IS NOT NULL OR team_id IS NOT NULL "
            "OR player_id IS NOT NULL OR nation_id IS NOT NULL",
            name="at_least_one_filter_present",
        ),
    )
