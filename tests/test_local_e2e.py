from app.cli import cli
from app.main import app
from fastapi.testclient import TestClient
from typer.testing import CliRunner


def test_local_e2e_when_docs_seeded_search_and_context_return_docs() -> None:
    runner = CliRunner()
    ingest = runner.invoke(
        cli,
        [
            "ingest",
            "--library",
            "/internal/platform",
            "--version",
            "main",
            "--source-dir",
            "examples/platform-docs",
        ],
    )
    client = TestClient(app)

    search = client.get(
        "/api/v2/libs/search",
        params={"query": "helm", "libraryName": "platform"},
    )
    context = client.get(
        "/api/v2/context",
        params={"libraryId": "/internal/platform", "query": "valuesFrom"},
    )

    assert ingest.exit_code == 0
    assert search.json()["results"][0]["id"] == "/internal/platform"
    assert "valuesFrom" in context.text
