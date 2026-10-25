import secrets

from sqlalchemy import CheckConstraint, Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.catalog import EventKind


def generate_ical_token() -> str:
    return secrets.token_urlsafe(32)


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    # IANA name (e.g. "America/Santiago"); events are stored in UTC and converted for display.
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", server_default="UTC")
    # The secret in the private iCal URL (ADR 0004). Regenerating it revokes the old URL.
    ical_token: Mapped[str] = mapped_column(String(64), unique=True, default=generate_ical_token)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")

    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="user", cascade="all, delete-orphan")


subscription_event_kinds = Table(
    "subscription_event_kinds",
    Base.metadata,
    Column("subscription_id", ForeignKey("subscriptions.id", ondelete="CASCADE"), primary_key=True),
    Column("event_kind_id", ForeignKey("event_kinds.id", ondelete="CASCADE"), primary_key=True),
)


class Subscription(TimestampMixin, Base):
    """A set of filters combined with AND; a user's subscriptions are combined with OR (design.md §4.3)."""

    __tablename__ = "subscriptions"
    __table_args__ = (
        # Enforced by the database, not just the API: a subscription needs at least one filter.
        CheckConstraint(
            "sport_id IS NOT NULL OR competition_id IS NOT NULL OR competitor_id IS NOT NULL OR nation_id IS NOT NULL",
            name="at_least_one_filter",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    sport_id: Mapped[int | None] = mapped_column(ForeignKey("sports.id", ondelete="CASCADE"))
    competition_id: Mapped[int | None] = mapped_column(ForeignKey("competitions.id", ondelete="CASCADE"))
    competitor_id: Mapped[int | None] = mapped_column(ForeignKey("competitors.id", ondelete="CASCADE"))
    nation_id: Mapped[int | None] = mapped_column(ForeignKey("nations.id", ondelete="CASCADE"))

    user: Mapped[User] = relationship(back_populates="subscriptions")
    # Empty = every kind of the sport.
    event_kinds: Mapped[list[EventKind]] = relationship(secondary=subscription_event_kinds)
