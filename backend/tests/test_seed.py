from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Competition, EventKind, Nation, Sport
from app.scripts.seed import seed

CATALOG = (Nation, Sport, EventKind, Competition)


def _counts(db: Session) -> dict[str, int]:
    return {model.__tablename__: db.scalar(select(func.count()).select_from(model)) for model in CATALOG}


def test_seed_is_idempotent(db: Session) -> None:
    seed(db)
    first = _counts(db)
    seed(db)

    assert _counts(db) == first
    assert first["sports"] == 2


def test_formula_1_defaults_to_qualifying_sprint_and_race(db: Session) -> None:
    seed(db)

    f1 = db.scalar(select(Sport).where(Sport.slug == "formula-1"))
    defaults = [kind.slug for kind in f1.event_kinds if kind.is_default]

    assert defaults == ["qualifying", "sprint", "race"]
