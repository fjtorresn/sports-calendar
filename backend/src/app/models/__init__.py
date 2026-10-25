"""Model registry.

Importing every model here guarantees that SQLAlchemy knows all of them (relationships
referenced by name, such as ``"EventParticipant"``) and that ``Base.metadata`` is complete
for Alembic, regardless of which ``app.models`` module is imported first.
"""

from app.models.base import Base
from app.models.catalog import Competition, Competitor, EventKind, Nation, Sport
from app.models.event import Event, EventParticipant
from app.models.ingestion import CompetitionExternalRef, CompetitorExternalRef, EventExternalRef, SyncState
from app.models.user import Subscription, User, subscription_event_kinds

__all__ = [
    "Base",
    "Competition",
    "CompetitionExternalRef",
    "Competitor",
    "CompetitorExternalRef",
    "Event",
    "EventExternalRef",
    "EventKind",
    "EventParticipant",
    "Nation",
    "Sport",
    "Subscription",
    "SyncState",
    "User",
    "subscription_event_kinds",
]
