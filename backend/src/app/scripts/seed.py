"""Seed the MVP catalog (design.md §2.4): sports, event kinds, nations and competitions.

Idempotent: every row is upserted by its natural key, so running it again updates names
instead of duplicating rows. Each competition is linked to its data source through a
CompetitionExternalRef. Competitors and events come from ingestion.

Usage: uv run python -m app.scripts.seed
"""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import Base, Competition, CompetitionExternalRef, EventKind, Nation, Sport
from app.models.enums import DataSource

NATIONS = [
    ("Argentina", "ARG"),
    ("Brazil", "BRA"),
    ("Chile", "CHI"),
    ("England", "ENG"),
    ("France", "FRA"),
    ("Germany", "GER"),
    ("Italy", "ITA"),
    ("Netherlands", "NED"),
    ("Portugal", "POR"),
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

# (slug, name, nation code or None, source, external id). football-data.org's free plan
# covers these 13 competitions (verified 2026-10-25); its external id is the competition code.
COMPETITIONS = {
    "football": [
        ("champions-league", "UEFA Champions League", None, DataSource.FOOTBALL_DATA, "CL"),
        ("copa-libertadores", "Copa Libertadores", None, DataSource.FOOTBALL_DATA, "CLI"),
        ("world-cup", "FIFA World Cup", None, DataSource.FOOTBALL_DATA, "WC"),
        ("european-championship", "European Championship", None, DataSource.FOOTBALL_DATA, "EC"),
        ("premier-league", "Premier League", "ENG", DataSource.FOOTBALL_DATA, "PL"),
        ("championship", "Championship", "ENG", DataSource.FOOTBALL_DATA, "ELC"),
        ("la-liga", "LaLiga", "ESP", DataSource.FOOTBALL_DATA, "PD"),
        ("bundesliga", "Bundesliga", "GER", DataSource.FOOTBALL_DATA, "BL1"),
        ("serie-a", "Serie A", "ITA", DataSource.FOOTBALL_DATA, "SA"),
        ("ligue-1", "Ligue 1", "FRA", DataSource.FOOTBALL_DATA, "FL1"),
        ("eredivisie", "Eredivisie", "NED", DataSource.FOOTBALL_DATA, "DED"),
        ("primeira-liga", "Primeira Liga", "POR", DataSource.FOOTBALL_DATA, "PPL"),
        ("brasileirao", "Campeonato Brasileiro Série A", "BRA", DataSource.FOOTBALL_DATA, "BSA"),
    ],
    "formula-1": [("world-championship", "Formula 1 World Championship", None, DataSource.JOLPICA, "f1")],
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
            for slug, name, code, _, _ in competitions
        ],
        ["sport_id", "slug"],
    )

    competition_ids = {
        (sport_slug, slug): id_
        for sport_slug, slug, id_ in db.execute(select(Sport.slug, Competition.slug, Competition.id).join(Sport))
    }
    _upsert(
        db,
        CompetitionExternalRef,
        [
            {"competition_id": competition_ids[sport, slug], "source": source, "external_id": external_id}
            for sport, competitions in COMPETITIONS.items()
            for slug, _, _, source, external_id in competitions
        ],
        ["source", "external_id"],
    )


def main() -> None:
    with SessionLocal() as db:
        seed(db)
        db.commit()
        for model in (Nation, Sport, EventKind, Competition, CompetitionExternalRef):
            print(f"{model.__tablename__}: {db.scalar(select(func.count()).select_from(model))}")


if __name__ == "__main__":
    main()
