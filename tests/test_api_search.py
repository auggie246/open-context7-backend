from app.main import app
from fastapi.testclient import TestClient


def test_search_endpoint_when_catalog_matches_returns_context7_shape() -> None:
    client = TestClient(app)

    response = client.get(
        "/api/v2/libs/search",
        params={"query": "helm valuesFrom", "libraryName": "platform", "fast": "true"},
    )

    assert response.status_code == 200
    assert response.json()["searchFilterApplied"] is False
    assert response.json()["results"][0]["id"] == "/internal/platform"


def test_search_endpoint_uses_query_not_library_name_only() -> None:
    client = TestClient(app)

    query_match = client.get(
        "/api/v2/libs/search",
        params={"query": "valuesFrom", "libraryName": "not-the-name"},
    )
    query_miss = client.get(
        "/api/v2/libs/search",
        params={"query": "unrelated-miss", "libraryName": "platform"},
    )

    assert query_match.status_code == 200
    assert query_match.json()["results"][0]["id"] == "/internal/platform"
    assert query_miss.status_code == 200
    assert query_miss.json()["results"] == []


def test_search_endpoint_when_required_params_missing_returns_422() -> None:
    client = TestClient(app)

    response = client.get("/api/v2/libs/search")

    assert response.status_code == 422
