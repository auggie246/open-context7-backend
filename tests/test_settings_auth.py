from collections.abc import Callable

import pytest
from app.auth import register_auth_exception_handler, require_bearer_auth
from app.settings import Settings, get_settings
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient


def make_client(settings_factory: Callable[[], Settings]) -> TestClient:
    app = FastAPI()
    register_auth_exception_handler(app)
    app.dependency_overrides[get_settings] = settings_factory

    def protected() -> dict[str, str]:
        return {"status": "ok"}

    _ = app.get("/protected", dependencies=[Depends(require_bearer_auth)])(protected)

    return TestClient(app)


def test_settings_reads_docs_prefixed_env_when_present(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOCS_API_KEYS", "alpha,beta")
    monkeypatch.setenv("DOCS_QDRANT_URL", "http://qdrant:6333")
    monkeypatch.setenv("DOCS_EMBEDDING_MODE", "local")
    monkeypatch.setenv("DOCS_MAX_CONTEXT_TOKENS", "9000")
    monkeypatch.setenv("DOCS_RERANKER_ENABLED", "true")

    settings = Settings()

    assert settings.api_keys == ["alpha", "beta"]
    assert settings.qdrant_url == "http://qdrant:6333"
    assert settings.embedding_mode == "local"
    assert settings.max_context_tokens == 9000
    assert settings.reranker_enabled is True


def test_auth_disabled_when_api_keys_empty() -> None:
    client = make_client(lambda: Settings(api_keys=[]))

    response = client.get("/protected")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_bearer_auth_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOCS_API_KEYS", "secret")
    get_settings.cache_clear()
    client = make_client(get_settings)

    missing_response = client.get("/protected")
    invalid_response = client.get("/protected", headers={"Authorization": "Bearer wrong"})
    valid_response = client.get("/protected", headers={"Authorization": "Bearer secret"})

    assert missing_response.status_code == 401
    assert missing_response.json() == {
        "error": "unauthorized",
        "message": "Bearer token required",
    }
    assert "X-Context7-Auth-Prompt" not in missing_response.headers
    assert invalid_response.status_code == 401
    assert invalid_response.json() == {
        "error": "unauthorized",
        "message": "Invalid bearer token",
    }
    assert "X-Context7-Auth-Prompt" not in invalid_response.headers
    assert valid_response.status_code == 200
    assert valid_response.json() == {"status": "ok"}
    get_settings.cache_clear()


def test_bearer_auth_uses_constant_time_comparison(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str]] = []

    def compare_digest(left: str, right: str) -> bool:
        calls.append((left, right))
        return left == right

    monkeypatch.setattr("app.auth.secrets.compare_digest", compare_digest)
    client = make_client(lambda: Settings(api_keys=["alpha", "secret", "omega"]))

    response = client.get("/protected", headers={"Authorization": "Bearer secret"})

    assert response.status_code == 200
    assert calls == [("secret", "alpha"), ("secret", "secret"), ("secret", "omega")]
