from app.ingest.models import DocChunk, DocChunkKind
from app.main import app
from app.store import save_chunks
from fastapi.testclient import TestClient


def seed_context_chunks() -> None:
    _ = save_chunks(
        [
            DocChunk(
                id="code-1",
                library_id="/internal/platform",
                version="main",
                source_path="guide.mdx",
                heading="Install",
                chunk_index=0,
                language="bash",
                kind=DocChunkKind.CODE,
                token_count=4,
                content="helm valuesFrom",
            )
        ]
    )


def test_context_endpoint_when_type_missing_returns_text() -> None:
    seed_context_chunks()
    client = TestClient(app)

    response = client.get(
        "/api/v2/context",
        params={"libraryId": "/internal/platform", "query": "valuesFrom"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "TITLE: Install" in response.text


def test_context_endpoint_when_json_returns_required_arrays() -> None:
    seed_context_chunks()
    client = TestClient(app)

    response = client.get(
        "/api/v2/context",
        params={"libraryId": "/internal/platform", "query": "valuesFrom", "type": "json"},
    )

    assert response.status_code == 200
    assert response.json()["codeSnippets"][0]["codeTitle"] == "Install"
    assert response.json()["infoSnippets"] == []


def test_context_endpoint_accepts_versioned_library_ids() -> None:
    seed_context_chunks()
    client = TestClient(app)

    slash_response = client.get(
        "/api/v2/context",
        params={"libraryId": "/internal/platform/main", "query": "valuesFrom"},
    )
    at_response = client.get(
        "/api/v2/context",
        params={"libraryId": "/internal/platform@main", "query": "valuesFrom"},
    )

    assert slash_response.status_code == 200
    assert "TITLE: Install" in slash_response.text
    assert at_response.status_code == 200
    assert "TITLE: Install" in at_response.text


def test_context_endpoint_when_library_unknown_returns_404() -> None:
    client = TestClient(app)

    response = client.get(
        "/api/v2/context",
        params={"libraryId": "/internal/missing", "query": "valuesFrom"},
    )

    assert response.status_code == 404
    assert response.json()["error"] == "not_found"
