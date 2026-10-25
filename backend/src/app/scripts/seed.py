"""Seed the MVP catalog (design.md §2.4): sports, event kinds, nations and competitions.

Idempotent: every row is upserted by its natural key, so running it again updates names
instead of duplicating rows. Competitors and events come from ingestion (phase 3).

Usage: uv run python -m app.scripts.seed
"""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import Base, Competition, EventKind, Nation, Sport

NATIONS = [
    ("Argentina", "ARG"),
    ("Chile", "CHI"),
    ("England", "ENG"),
    ("France", "FRA"),
    ("Germany", "GER"),
    ("Italy", "ITA"),
    ("Spain", "ESP"),
]

SPORTS = [("football", "Football"), ("formula-1", "Formula 1")]

# (slug, name, is_default) in display order. Defaults are what the UI preselects.
EVENT_KINDS = {
    "football": [("match", "Match", True)],
    "formula-1": [
        ("practice", "Practice", False),
        ("sprint_qualifying", "Sprint qualifying", False),
        ("qualifying", "Qualifying", True),
        ("sprint", "Sprint", True),
        ("race", "Race", True),
    ],
}

# (slug, name, nation code or None for international competitions)
COMPETITIONS = {
    "football": [
        ("champions-league", "UEFA Champions League", None),
        ("la-liga", "LaLiga", "ESP"),
        ("premier-league", "Premier League", "ENG"),
    ],
    "formula-1": [("world-championship", "Formula 1 World Championship", None)],
}


def _upsert(db: Session, model: type[Base], rows: Sequence[dict[str, Any]], key: list[str]) -> None:
    stmt = insert(model).values(list(rows))
    updates = {column: stmt.excluded[column] for column in rows[0] if column not in key}
    db.execute(stmt.on_conflict_do_update(index_elements=key, set_=updates))


def seed(db: Session) -> None:
    _upsert(db, Nation, [{"name": name, "code": code} for name, code in NATIONS], ["code"])
    _upsert(db, Sport, [{"slug": slug, "name": name} for slug, name in SPORTS], ["slug"])

    sport_ids = dict(db.execute(select(Sport.slug, Sport.id)).all())
    nation_ids = dict(db.execute(select(Nation.code, Nation.id)).all())

    _upsert(
        db,
        EventKind,
        [
            {"sport_id": sport_ids[sport], "slug": slug, "name": name, "is_default": default, "display_order": i}
            for sport, kinds in EVENT_KINDS.items()
            for i, (slug, name, default) in enumerate(kinds)
        ],
        ["sport_id", "slug"],
    )
    _upsert(
        db,
        Competition,
        [
            {"sport_id": sport_ids[sport], "slug": slug, "name": name, "nation_id": nation_ids.get(code)}
            for sport, competitions in COMPETITIONS.items()
            for slug, name, code in competitions
        ],
        ["sport_id", "slug"],
    )


def main() -> None:
    with SessionLocal() as db:
        seed(db)
        db.commit()
        for model in (Nation, Sport, EventKind, Competition):
            print(f"{model.__tablename__}: {db.scalar(select(func.count()).select_from(model))}")


if __name__ == "__main__":
    main()
