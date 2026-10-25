"""Model registry.

Importing every model here guarantees that SQLAlchemy knows all of them (relationships
referenced by name, such as ``"User"``) and that ``Base.metadata`` is complete for Alembic,
regardless of which ``app.models`` module is imported first.
"""

from app.models.event import Event, EventParticipant
from app.models.sports import Competition, Nation, Player, Sport, Team
from app.models.user import User, UserSubscription

__all__ = [
    "Competition",
    "Event",
    "EventParticipant",
    "Nation",
    "Player",
    "Sport",
    "Team",
    "User",
    "UserSubscription",
]
