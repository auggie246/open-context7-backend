# Open Context7 Backend Configuration

Purpose: list the current `DOCS_` environment variables used by Open Context7 Backend.

Source of truth: `.env.example`, `app/settings.py`, `docker-compose.yml`, and `tests/test_settings_auth.py`.

## Loading Rules

Settings are defined in `app/settings.py` with the `DOCS_` prefix and optional `.env` loading. Empty environment values are ignored. Nested delimiter support is configured, but current settings are flat.

`DOCS_API_KEYS` is parsed specially: a comma-separated string of one or more keys is split into configured bearer tokens, with surrounding whitespace removed and empty entries ignored.

## Variables

| Variable | Default | Source | Meaning |
| --- | --- | --- | --- |
| `DOCS_API_KEYS` | unset in code; `.env.example` and Compose use `dev-local-secret` | `.env.example`, `app/settings.py`, `docker-compose.yml` | Comma-separated bearer tokens. When empty, API auth is disabled. |
| `DOCS_QDRANT_URL` | `http://localhost:6333` | `.env.example`, `app/settings.py`, `docker-compose.yml` | Qdrant HTTP URL. Compose points the API container at `http://qdrant:6333`. |
| `DOCS_RETRIEVAL_MODE` | `lexical` | `app/settings.py`, `docker-compose.yml` | Retrieval backend. Allowed values are `lexical` and `qdrant`. Compose sets `qdrant`. |
| `DOCS_EMBEDDING_MODE` | `deterministic` | `.env.example`, `app/settings.py`, `docker-compose.yml` | Embedding mode marker for the current deterministic embedding implementation. |
| `DOCS_MAX_CONTEXT_TOKENS` | `5000` | `.env.example`, `app/settings.py` | Parsed maximum context token budget setting. The current context route still uses a fixed 5000-token budget unless the route is wired differently. |
| `DOCS_RERANKER_ENABLED` | `false` | `.env.example`, `app/settings.py`, `docker-compose.yml` | Parsed boolean flag. The current reranker implementation is pass-through. |

## Example `.env`

```sh
DOCS_API_KEYS=dev-local-secret
DOCS_QDRANT_URL=http://localhost:6333
DOCS_RETRIEVAL_MODE=lexical
DOCS_EMBEDDING_MODE=deterministic
DOCS_MAX_CONTEXT_TOKENS=5000
DOCS_RERANKER_ENABLED=false
```

`.env.example` does not currently include `DOCS_RETRIEVAL_MODE`; the setting still exists in `app/settings.py` and defaults to `lexical`.

## Docker Compose Defaults

`docker-compose.yml` builds the FastAPI backend image for `docs-api` and runs
Qdrant as a separate Qdrant service from `qdrant/qdrant:v1.12.6`; Qdrant is not
built into the app image.

`docker-compose.yml` runs the API with:

- `DOCS_QDRANT_URL=http://qdrant:6333`
- `DOCS_RETRIEVAL_MODE=qdrant`
- `DOCS_EMBEDDING_MODE=deterministic`
- `DOCS_RERANKER_ENABLED=false`
- `DOCS_API_KEYS=${DOCS_API_KEYS:-dev-local-secret}`

Compose binds API and Qdrant to `127.0.0.1` on ports `8000` and `6333`.
Inside Compose, `docs-api` reaches Qdrant at `DOCS_QDRANT_URL=http://qdrant:6333`.
Qdrant persists data in the `qdrant-data` named volume; `docker compose down`
keeps it, and `docker compose down -v` removes it intentionally.

## Gotchas

- Empty `DOCS_API_KEYS` disables auth; Compose sets `dev-local-secret` by default.
- `DOCS_RETRIEVAL_MODE=qdrant` also needs a reachable Qdrant service and ingested chunks in the shared `docs` collection.
- `DOCS_MAX_CONTEXT_TOKENS` is parsed by settings, but current route behavior still uses the fixed 5000-token context budget.
- `DOCS_RERANKER_ENABLED` is parsed, but current reranker behavior is pass-through.

## Verification

Useful focused checks:

```sh
rg -q 'DOCS_API_KEYS|DOCS_QDRANT_URL|DOCS_RETRIEVAL_MODE|DOCS_EMBEDDING_MODE|DOCS_MAX_CONTEXT_TOKENS|DOCS_RERANKER_ENABLED' docs/configuration.md
DOCS_API_KEYS=dev-local-secret PYTHONDONTWRITEBYTECODE=1 uv run pytest -q -p no:cacheprovider tests/test_settings_auth.py
```

## Next

- Read [auth](auth.md) for bearer-token behavior.
- Read [retrieval](retrieval.md) for retrieval mode details.
