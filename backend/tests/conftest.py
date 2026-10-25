from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.main import app
from app.core.database import SessionLocal


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db() -> Iterator[Session]:
    """Session against the test database; everything the test does is rolled back."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
