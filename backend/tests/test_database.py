from sqlalchemy import text
from sqlalchemy.orm import Session


def test_database_is_reachable(db: Session) -> None:
    """Verifica que los tests corren contra un PostgreSQL real (RNF-8)."""
    assert db.execute(text("SELECT 1")).scalar_one() == 1


def test_database_is_postgresql(db: Session) -> None:
    version = db.execute(text("SELECT version()")).scalar_one()

    assert version.startswith("PostgreSQL")
