from app.main import app
from fastapi.testclient import TestClient


def test_app_title_when_imported() -> None:
    assert app.title == "Open Context7 Backend"


def test_healthz_when_called_returns_ok() -> None:
    client = TestClient(app)

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
