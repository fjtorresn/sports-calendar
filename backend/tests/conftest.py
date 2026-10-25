from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import Session

from app.api.main import app
from app.core.config import get_settings
from app.core.database import get_db

BACKEND_DIR = Path(__file__).resolve().parents[1]


def _test_database_url() -> URL:
    """A dedicated database, so tests never touch development data."""
    url = make_url(get_settings().database_url)
    if not url.database.endswith("_test"):
        url = url.set(database=f"{url.database}_test")
    return url


def _recreate_database(url: URL) -> None:
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{url.database}" WITH (FORCE)'))
        conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    admin.dispose()


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    """Fresh database per test run, built by the real migrations (which tests them too)."""
    url = _test_database_url()
    _recreate_database(url)

    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", url.render_as_string(hide_password=False))
    command.upgrade(config, "head")

    engine = create_engine(url)
    yield engine
    engine.dispose()


@pytest.fixture
def db(engine: Engine) -> Iterator[Session]:
    """Session inside a transaction that is rolled back after each test.

    ``create_savepoint`` lets the code under test call ``commit()`` freely: it only
    releases a savepoint, and the outer rollback still undoes everything.
    """
    with engine.connect() as connection:
        transaction = connection.begin()
        session = Session(bind=connection, join_transaction_mode="create_savepoint")
        try:
            yield session
        finally:
            session.close()
            transaction.rollback()


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: db
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()
