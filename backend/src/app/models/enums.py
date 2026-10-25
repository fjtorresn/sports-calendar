"""Fixed-value domains, stored as VARCHAR + CHECK (see ADR 0005)."""

from enum import StrEnum

from sqlalchemy import Enum


class CompetitorKind(StrEnum):
    TEAM = "team"
    INDIVIDUAL = "individual"


class EventStatus(StrEnum):
    SCHEDULED = "scheduled"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"
    FINISHED = "finished"


class TimePrecision(StrEnum):
    EXACT = "exact"
    NOT_BEFORE = "not_before"
    DATE_ONLY = "date_only"


class SyncStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"


class DataSource(StrEnum):
    FOOTBALL_DATA = "football_data"
    JOLPICA = "jolpica"


def string_enum(enum_cls: type[StrEnum]) -> Enum:
    """Column type for a StrEnum: VARCHAR plus a CHECK listing the allowed values.

    ``values_callable`` stores the enum *values* ("not_before"), not the member names
    ("NOT_BEFORE"), so the database stays readable without the Python code.
    """
    return Enum(
        enum_cls,
        name=enum_cls.__name__.lower(),
        native_enum=False,
        create_constraint=True,
        length=max(len(member.value) for member in enum_cls),
        values_callable=lambda cls: [member.value for member in cls],
    )
