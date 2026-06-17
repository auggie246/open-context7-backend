# Open Context7 Backend

Open Context7 Backend is a Python 3.12+ FastAPI service that serves a
Context7-compatible wire contract from local Markdown and MDX sources. It is
for teams that want deterministic ingestion, catalog metadata in Git, local
lexical retrieval by default, and optional Qdrant retrieval without hosted
documentation infrastructure.

SDK-compatible means backend wire contract compatible only. The stock
TypeScript SDK hardcodes its base URL, so SDK end-to-end repointing is out of
scope for this backend.

## When To Use It

Use this backend when you need:

- A local or air-gapped documentation API for curated internal docs.
- Catalog-driven library metadata from `libraries/*.yaml`.
- Deterministic Markdown/MDX parsing without LLM-based snippet extraction.
- Local lexical retrieval for simple local use, or Qdrant retrieval for
  vector-backed lookup.
- A small Context7-compatible HTTP contract for search and context responses.

This repository is not a hosted docs product, crawler, identity platform, or web
UI.

## Prerequisites

- Python 3.12 or newer.
- `uv` for dependency management and command execution.
- Docker and Docker Compose only when using Qdrant or the Compose stack.
- Local documentation sources, either the example docs in `examples/` or a
  catalog entry under `libraries/`.

## Quick Start

```sh
uv sync
uv run context7-backend ingest --library /internal/platform --version main --source-dir examples/platform-docs
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
curl -f http://localhost:8000/healthz
```

The example ingest writes deterministic local chunks. With default settings,
the API reads those chunks using local lexical retrieval.

## MCP Setup

Set the API URL for the stock `@upstash/context7-mcp` package:

```sh
export CONTEXT7_API_URL=http://localhost:8000/api
```

The MCP package appends `/v2/...` when it calls the backend. If
`DOCS_API_KEYS` is configured, MCP or any other client must send
`Authorization: Bearer <key>` for `/api/v2/*` requests.

## HTTP API Examples

Search catalog libraries:

```sh
curl 'http://localhost:8000/api/v2/libs/search?query=platform&libraryName=platform&fast=true'
```

Fetch text snippets:

```sh
curl 'http://localhost:8000/api/v2/context?libraryId=/internal/platform&query=valuesFrom'
```

Fetch JSON snippets:

```sh
curl 'http://localhost:8000/api/v2/context?libraryId=/internal/platform&query=valuesFrom&type=json'
```

`GET /healthz` is intentionally unauthenticated. `GET /api/v2/libs/search` and
`GET /api/v2/context` require bearer auth when API keys are configured.

## Ingestion Workflow

Catalog metadata lives in `libraries/*.yaml`. Ingest from a catalog-backed
source with:

```sh
uv run context7-backend ingest --library /internal/platform --version main --source-dir examples/platform-docs
```

The parser is deterministic and stores chunks for retrieval. See
[ingestion](docs/ingestion.md) for parser rules, stable chunk IDs, orphan
replacement, and symlink containment.

## Configuration

Runtime settings use `DOCS_` environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `DOCS_API_KEYS` | empty | Comma-separated bearer tokens. Empty disables auth. |
| `DOCS_RETRIEVAL_MODE` | `lexical` | `lexical` or `qdrant`. |
| `DOCS_QDRANT_URL` | `http://localhost:6333` | Qdrant endpoint for qdrant mode. |
| `DOCS_EMBEDDING_MODE` | `deterministic` | Embedding mode currently used by Qdrant ingestion/query. |
| `DOCS_MAX_CONTEXT_TOKENS` | `5000` | Parsed context token budget setting; the current context route still uses a fixed 5000-token budget. |
| `DOCS_RERANKER_ENABLED` | `false` | Reranker flag; current reranker behavior is pass-through. |

See [configuration](docs/configuration.md) for the full local configuration
surface.

## Auth

Auth is disabled until `DOCS_API_KEYS` is set. When keys are configured, every
`/api/v2/*` request must include:

```http
Authorization: Bearer <key>
```

Configured keys are checked with constant-time comparison. The service never
emits `X-Context7-Auth-Prompt`; clients should rely on normal HTTP 401
responses. See [auth](docs/auth.md) for Compose defaults and unsupported auth
schemes.

## Retrieval Modes

Local lexical retrieval reads local chunks and ranks matches deterministically.
Qdrant retrieval uses the shared `docs` collection with payload indexes for
`library_id`, `version`, `kind`, and `source_path`.

See [retrieval](docs/retrieval.md) for filters, token budgets, Qdrant behavior,
and reranker limitations.

## Docker Compose

Run the API and Qdrant locally:

```sh
docker compose up -d --build docs-api qdrant
curl -f http://localhost:8000/healthz
docker compose down
```

The Dockerfile builds only the FastAPI backend image. Qdrant is not built into
the app image and does not run from the backend container; Compose starts a
separate Qdrant service from `qdrant/qdrant:v1.12.6`.

Compose binds the API to `127.0.0.1:8000` and Qdrant to `127.0.0.1:6333`.
Inside Compose, `docs-api` reaches Qdrant at
`DOCS_QDRANT_URL=http://qdrant:6333`. It sets
`DOCS_RETRIEVAL_MODE=qdrant`, deterministic embeddings, and
`DOCS_API_KEYS=${DOCS_API_KEYS:-dev-local-secret}`. Calls to `/api/v2/*` need
`Authorization: Bearer dev-local-secret` unless you override the key.

Qdrant data lives in the named `qdrant-data` volume. `docker compose down`
stops containers and preserves volume; `docker compose down -v` removes
intentionally.

## Development And QA

Common commands:

```sh
PYTHONDONTWRITEBYTECODE=1 uv run pytest -q -p no:cacheprovider
uv run ruff check app tests
uv run basedpyright app tests
scripts/verify_code_quality.sh
scripts/qa_http_contract.sh
scripts/qa_mcp_contract.sh
scripts/qa_qdrant_contract.sh
```

If QA starts services, clean them up and verify ports `8000` and `6333` are no
longer bound before finishing.

## Detailed Docs

- [Architecture](docs/architecture.md): request flow, data flow, and component
  boundaries.
- [API](docs/api.md): HTTP endpoints, parameters, response shapes, and errors.
- [Ingestion](docs/ingestion.md): CLI ingest behavior, parsing, chunk IDs, and
  source containment.
- [Catalog](docs/catalog.md): `libraries/*.yaml`, library IDs, versions,
  aliases, and validation.
- [Retrieval](docs/retrieval.md): lexical and Qdrant modes, filters, indexes,
  token budgets, and reranking.
- [Configuration](docs/configuration.md): supported environment variables.
- [Auth](docs/auth.md): bearer auth, disabled-by-default behavior, and 401s.
- [Deployment](docs/deployment.md): local uvicorn and Docker Compose operation.
- [Development](docs/development.md): project layout and local development.
- [Testing](docs/testing.md): targeted tests and QA scripts.
- [Troubleshooting](docs/troubleshooting.md): common failures and where to look.

## Troubleshooting

Start with [troubleshooting](docs/troubleshooting.md). The most common issues
are missing catalog entries, stale local chunks, missing bearer tokens, Qdrant
readiness, port conflicts on `8000` or `6333`, and symlink escape rejections
during ingest.

## Scope Boundaries

The following are out of scope for the current v1 backend or not available:

- Web UI.
- OIDC, OpenID, or team auth.
- Kubernetes deployment or manifests.
- HTML or sitemap crawling.
- LLM-based snippet extraction.
- Vendored `@upstash/context7-mcp` source edits.
