# Open Context7 Backend Deployment

Purpose: document the supported local deployment paths for Open Context7 Backend.

Source of truth: `Dockerfile`, `docker-compose.yml`, `app/main.py`, `app/settings.py`, and `AGENTS.md`.

## Supported Paths

This repository currently documents two deployment modes:

- Local `uvicorn` for development and small local use.
- Docker Compose with the API plus Qdrant.

Kubernetes, k8s manifests, hosted multi-tenant deployment, OIDC/team auth, and a web UI are not implemented and are out of scope for this backend.

## Local Uvicorn

Run the API directly from the repository:

```sh
uv sync
uv run context7-backend ingest --library /internal/platform --version main --source-dir examples/platform-docs
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
curl -f http://127.0.0.1:8000/healthz
```

With default settings, retrieval uses local lexical retrieval and reads `.omo/local-store/chunks.json`. Auth is disabled unless `DOCS_API_KEYS` is set.

For authenticated local testing:

```sh
DOCS_API_KEYS=dev-local-secret uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
curl -H 'Authorization: Bearer dev-local-secret' \
  'http://127.0.0.1:8000/api/v2/libs/search?query=platform&libraryName=platform'
```

`/healthz` remains unauthenticated. `/api/v2/*` requires bearer auth only when `DOCS_API_KEYS` is configured.

## Docker Image

`Dockerfile` uses `ghcr.io/astral-sh/uv:python3.12-bookworm-slim`, copies `app`, `libraries`, and `examples`, installs frozen non-dev dependencies, exposes port `8000`, and starts:

```sh
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The container listens on `0.0.0.0` internally so Docker can publish it. Compose binds it only to loopback on the host.

## Docker Compose

Start the API and Qdrant:

```sh
docker compose up -d --build docs-api qdrant
curl -f http://127.0.0.1:8000/healthz
curl -H 'Authorization: Bearer dev-local-secret' \
  'http://127.0.0.1:8000/api/v2/libs/search?query=platform&libraryName=platform'
docker compose down
```

Compose host bindings:

- API: `127.0.0.1:8000`
- Qdrant: `127.0.0.1:6333`

Compose API settings:

- `DOCS_QDRANT_URL=http://qdrant:6333`
- `DOCS_RETRIEVAL_MODE=qdrant`
- `DOCS_EMBEDDING_MODE=deterministic`
- `DOCS_RERANKER_ENABLED=false`
- `DOCS_API_KEYS=${DOCS_API_KEYS:-dev-local-secret}`

Because Compose sets `DOCS_API_KEYS` by default, `/api/v2/*` calls need `Authorization: Bearer dev-local-secret` unless the key is overridden. `/healthz` is still open for health checks.

## Qdrant Volume

`docker-compose.yml` declares a named volume:

```yaml
volumes:
  qdrant-data:
```

Qdrant stores data at `/qdrant/storage` inside the container. `docker compose down` stops and removes containers but keeps the named volume. Use this only when you intentionally want to remove stored Qdrant data:

```sh
docker compose down -v
```

## Cleanup

If Compose or QA starts services, finish with:

```sh
docker compose down
! lsof -i :8000
! lsof -i :6333
```

If either port is still bound, identify the owning process before starting another local API or Qdrant instance.

## Gotchas

- Local `uvicorn` defaults to local lexical retrieval unless environment variables select Qdrant retrieval.
- Compose defaults to Qdrant retrieval and a bearer token.
- Qdrant readiness is not the same as API readiness; check both `http://127.0.0.1:6333/collections` and `http://127.0.0.1:8000/healthz` when debugging Compose.
- Do not edit or mount `src/context7--upstash-context7-mcp-3.2.1` as deployment source. It is vendored reference material.

## Verification

Useful focused checks:

```sh
test -s docs/deployment.md
rg -q 'docker compose up -d --build docs-api qdrant|127.0.0.1:8000|127.0.0.1:6333|docker compose down' docs/deployment.md
```

## Next

- Read [configuration](configuration.md) for Compose environment defaults.
- Read [testing](testing.md) for HTTP, MCP, and Qdrant QA scripts.
