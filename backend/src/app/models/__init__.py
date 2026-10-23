"""Registro de modelos.

Importar todos los modelos aquí garantiza que SQLAlchemy los conozca a todos
(relaciones por nombre como ``"User"``) y que ``Base.metadata`` esté completo para Alembic,
sin importar qué módulo de ``app.models`` se importe primero.
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
