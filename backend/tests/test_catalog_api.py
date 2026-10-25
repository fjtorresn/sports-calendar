from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.scripts.seed import seed


def test_lists_sports(client: TestClient, db: Session) -> None:
    seed(db)

    response = client.get("/api/v1/catalog/sports")

    assert response.status_code == 200
    assert [s["slug"] for s in response.json()] == ["football", "formula-1"]


def test_lists_event_kinds_in_display_order(client: TestClient, db: Session) -> None:
    seed(db)

    response = client.get("/api/v1/catalog/sports/formula-1/event-kinds")

    assert [k["slug"] for k in response.json()] == ["practice", "sprint_qualifying", "qualifying", "sprint", "race"]


def test_unknown_sport_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/catalog/sports/curling/event-kinds")

    assert response.status_code == 404


def test_lists_competitions_of_a_sport(client: TestClient, db: Session) -> None:
    seed(db)

    response = client.get("/api/v1/catalog/sports/football/competitions")

    assert {c["slug"] for c in response.json()} == {"champions-league", "la-liga", "premier-league"}
