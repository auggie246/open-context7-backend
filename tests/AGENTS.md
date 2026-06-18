# TESTS KNOWLEDGE BASE

**Generated:** 2026-06-18

## OVERVIEW

Pytest suite organized by behavior surface: API, ingest, retrieval, formatting, docs contracts, deployment, and one local e2e path.

## WHERE TO LOOK

| Surface | Files | Notes |
| --- | --- | --- |
| API | `test_api_search.py`, `test_api_context.py` | Context7 response contracts |
| Auth/settings | `test_settings_auth.py`, `test_scaffold.py` | env parsing, health, bearer boundaries |
| Ingest/parser | `test_parser.py`, `test_ingest_cli.py`, `test_ingest_repository.py` | deterministic chunks, excludes, symlink escapes |
| Retrieval | `test_retrieval_lexical.py`, `test_qdrant_adapter.py`, `test_embeddings_rerank.py` | ranking, token budget, Qdrant filters |
| Formatting/models | `test_format_json.py`, `test_format_text.py`, `test_models.py` | wire shapes and defaults |
| Catalog/docs/deploy | `test_catalog.py`, `test_docs_contract.py`, `test_deployment_compose.py` | YAML, docs markers, Docker contracts |
| E2E | `test_local_e2e.py` | ingest then search/context |
| Fixtures | `fixtures/` | catalog YAML and MDX docs |

## CONVENTIONS

- Tests build small data inline with per-file helpers; there is no shared global fixture layer.
- Use `tmp_path` for filesystem state and `monkeypatch` for environment changes.
- HTTP tests use `fastapi.testclient.TestClient`; CLI tests use `typer.testing.CliRunner`.
- Preserve explicit boundary tests for auth, symlink containment, Qdrant filters, formatter shape, and docs/source markers.
- Add focused tests only for new behavior or subtle bug fixes; keep test names behavior-driven.

## ANTI-PATTERNS

- Do not remove or weaken tests to fit an implementation.
- Do not let pytest generate bytecode under `app` or `tests`; use `PYTHONDONTWRITEBYTECODE=1`.
- Do not hide broad behavior changes inside docs contract or scaffold tests.
- Do not make tests depend on live Qdrant unless they are explicit contract scripts outside pytest.

## COMMANDS

```bash
PYTHONDONTWRITEBYTECODE=1 rtk uv run pytest -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 rtk uv run pytest -q -p no:cacheprovider tests/test_ingest_cli.py
PYTHONDONTWRITEBYTECODE=1 rtk uv run pytest -q -p no:cacheprovider tests/test_settings_auth.py
PYTHONDONTWRITEBYTECODE=1 rtk uv run pytest -q -p no:cacheprovider tests/test_docs_contract.py
```
