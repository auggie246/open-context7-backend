# Open Context7 Backend

Python FastAPI service that implements the Context7-compatible backend wire contract for local and air-gapped documentation.

## Development

```sh
uv run pytest -q
uv run ruff check app tests
uv run basedpyright app tests
uv run context7-backend ingest --library /internal/platform --version main --source-dir examples/platform-docs
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Set `CONTEXT7_API_URL=http://localhost:8000/api` for stock `@upstash/context7-mcp`; the MCP package appends `/v2/...`.

## Endpoints

`GET /healthz` returns service health.

`GET /api/v2/libs/search?query=<task>&libraryName=<name>&fast=true` searches YAML catalog files under `libraries/` and returns Context7 library objects with `searchFilterApplied:false`.

`GET /api/v2/context?libraryId=/internal/platform&query=valuesFrom` returns `text/plain` Context7-style snippets. Missing `type` and `type=txt` both use text mode.

`GET /api/v2/context?libraryId=/internal/platform&query=valuesFrom&type=json` returns OpenAPI-compatible `codeSnippets` and `infoSnippets` arrays.

SDK-compatible means backend wire contract compatible only. The stock TypeScript SDK hardcodes its base URL, so SDK end-to-end repointing is out of scope for this backend.

## Ingestion

YAML files under `libraries/` are the v1 source of truth for library metadata. Local docs are ingested with:

```sh
uv run context7-backend ingest --library /internal/platform --version main --source-dir examples/platform-docs
```

Markdown and MDX parsing is deterministic: frontmatter and MDX JSX/imports are tolerated, fenced code blocks are preserved, and stable chunk IDs make re-ingestion idempotent with orphan replacement for the same library/version.

## Retrieval

Local mode uses deterministic lexical retrieval over stored chunks with stable ordering by `source_path`, `heading`, and `chunk_index`. Qdrant support uses a shared `docs` collection and creates payload indexes for `library_id`, `version`, `kind`, and `source_path`.

## Auth

Auth is disabled unless `DOCS_API_KEYS` is set. When configured, requests to `/api/v2/*` must include `Authorization: Bearer <key>` or the API returns `401 {"error":"unauthorized","message":"..."}`. The service never emits `X-Context7-Auth-Prompt`.

## Compose

```sh
docker compose up -d --build docs-api qdrant
curl -f http://localhost:8000/healthz
docker compose down
```

Compose runs `docs-api` and Qdrant with deterministic embedding mode by default. Qdrant persistence uses the `qdrant-data` volume.
Both host ports bind to `127.0.0.1` for local development. Compose also sets
`DOCS_API_KEYS=${DOCS_API_KEYS:-dev-local-secret}`, so API calls to `/api/v2/*`
need `Authorization: Bearer dev-local-secret` unless you override the key.

## Scope Boundaries

No web UI is implemented. OIDC/team auth, HTML/sitemap crawling, Kubernetes manifests, LLM-based snippet extraction, and vendored `@upstash/context7-mcp` edits are out of scope for v1.
