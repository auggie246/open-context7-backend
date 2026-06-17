# Open Context7 Backend Testing

Purpose: document the tests and QA scripts used to verify Open Context7 Backend.

Source of truth: `tests/test_docs_contract.py`, `scripts/verify_code_quality.sh`, `scripts/qa_http_contract.sh`, `scripts/qa_mcp_contract.sh`, `scripts/qa_qdrant_contract.sh`, `scripts/qa_full.sh`, and `AGENTS.md`.

## Targeted Docs Checks

The focused docs contract test is:

```sh
PYTHONDONTWRITEBYTECODE=1 uv run pytest -q -p no:cacheprovider tests/test_docs_contract.py
```

For docs-only edits, also use direct file and marker checks that match the acceptance criteria for the docs task being changed. Example:

```sh
test -s docs/deployment.md
rg -q 'docker compose up -d --build docs-api qdrant|127.0.0.1:8000|127.0.0.1:6333|docker compose down' docs/deployment.md
```

These checks prove the intended docs surface directly instead of relying on unrelated app behavior.

## Code Quality Gate

Run:

```sh
scripts/verify_code_quality.sh
```

The script sets `PYTHONDONTWRITEBYTECODE=1`, deletes bytecode artifacts under `app` and `tests`, runs:

```sh
uv run ruff check app tests
uv run basedpyright app tests
uv run pytest -q -p no:cacheprovider
```

Then it checks that no `__pycache__` or `.pyc` files remain under `app` or `tests`.

## Focused Test Commands

Common targeted commands:

```sh
PYTHONDONTWRITEBYTECODE=1 uv run pytest -q -p no:cacheprovider tests/test_api_search.py
PYTHONDONTWRITEBYTECODE=1 uv run pytest -q -p no:cacheprovider tests/test_api_context.py
PYTHONDONTWRITEBYTECODE=1 uv run pytest -q -p no:cacheprovider tests/test_ingest_cli.py
PYTHONDONTWRITEBYTECODE=1 uv run pytest -q -p no:cacheprovider tests/test_parser.py
PYTHONDONTWRITEBYTECODE=1 uv run pytest -q -p no:cacheprovider tests/test_settings_auth.py
```

Use targeted tests for the surface being changed, then broaden to the quality gate when code behavior changes.

## HTTP Contract QA

Run:

```sh
scripts/qa_http_contract.sh
```

The script ingests `examples/platform-docs`, starts `uvicorn` on `127.0.0.1:8000`, calls `/api/v2/libs/search` and `/api/v2/context`, checks text and JSON responses, checks no-match output, checks versioned library IDs, checks an auth 401 path, cleans up the server, and requires `HTTP QA APPROVED`.

## MCP Contract QA

Run:

```sh
scripts/qa_mcp_contract.sh
```

The script builds the vendored `@upstash/context7-mcp` reference package for contract QA, ingests example docs, starts the backend, runs `scripts/qa_mcp_contract.mjs`, requires `MCP QA APPROVED`, and cleans up the backend process. The vendored tree remains reference material; do not edit it as part of docs or app changes.

## Qdrant Contract QA

Run:

```sh
scripts/qa_qdrant_contract.sh
```

Qdrant runs as a separate Compose service from `qdrant/qdrant:v1.12.6`; it is
not built into the FastAPI backend image. Compose integration checks
verify `docs-api` uses `DOCS_QDRANT_URL=http://qdrant:6333`, host ports stay
loopback-bound to `127.0.0.1:8000` and `127.0.0.1:6333`, `qdrant-data`
volume persists after `docker compose down`, and `docker compose down -v`
is used only when intentionally removing Qdrant data.

The script starts Qdrant with Docker Compose, waits
`http://127.0.0.1:6333/collections`, runs the Qdrant smoke command, ingests
example docs with `DOCS_RETRIEVAL_MODE=qdrant`, starts the API on
`127.0.0.1:8000`, calls `/api/v2/context`, prints `QDRANT QA APPROVED`, and
tears down with `docker compose down`.

## Why `qa_full.sh` Is Not Split-Qdrant Proof

Scope: `scripts/qa_full.sh` verifies broad repository behavior, not
split-Qdrant Compose plan proof. The The plan compliance path remains
`.omo/plans/context7-backend-reverse-engineer.md` through
`scripts/verify_plan_compliance.sh`; a successful run does not prove
`.omo/plans/split-qdrant-compose.md` acceptance criteria.

Proof set: `tests/test_docs_contract.py`, `tests/test_deployment_compose.py`,
focused `rg` checks, and captured split-Qdrant Compose evidence. HTTP, MCP, and
Qdrant QA scripts cover documented example contract surfaces that need
real-service verification.

## Cleanup Checks

Any QA command that starts services must clean them up. After HTTP, MCP, or Qdrant smoke runs, check:

```sh
! lsof -i :8000
! lsof -i :6333
```

Compose defaults `/api/v2/*` auth to `Authorization: Bearer dev-local-secret`;
missing auth can make a healthy stack look broken.

If a port remains bound, identify and clean up the process or container before finishing.

## Gotchas

- Treat `scripts/qa_full.sh` as broad QA, not split-Qdrant Compose plan proof.
- A successful script banner is not enough if a service remains bound afterward.
- Use `PYTHONDONTWRITEBYTECODE=1` for pytest commands to avoid bytecode artifacts under `app` and `tests`.

## Verification

Useful focused checks:

```sh
rg -q 'qa_http_contract.sh|qa_mcp_contract.sh|qa_qdrant_contract.sh' docs/testing.md
rg -q 'split-Qdrant|split-qdrant|Compose architecture|qa_full.sh.*context7-backend-reverse-engineer' docs/testing.md
```

## Next

- Read [development](development.md) for local development commands.
- Read [deployment](deployment.md) for service startup and cleanup.
