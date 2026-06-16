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

The script starts Qdrant with Docker Compose, waits for `http://127.0.0.1:6333/collections`, runs the Qdrant smoke command, ingests example docs with `DOCS_RETRIEVAL_MODE=qdrant`, starts the API on `127.0.0.1:8000`, calls `/api/v2/context`, prints `QDRANT QA APPROVED`, and tears down with `docker compose down`.

## Why `qa_full.sh` Is Not Docs-Only Proof

`scripts/qa_full.sh` is useful for broad repository verification, but it is not the docs-only proof for this documentation-upgrade plan. `scripts/qa_full.sh` still references `.omo/plans/context7-backend-reverse-engineer.md` through `scripts/verify_plan_compliance.sh`, so a successful run does not prove the targeted documentation-upgrade acceptance criteria.

For this plan, docs-only proof should combine `tests/test_docs_contract.py` with exact `test -s` and `rg` checks for the docs files being changed. Use HTTP, MCP, and Qdrant QA scripts when the documented examples or contract surfaces need real-service verification.

## Cleanup Checks

Any QA command that starts services must clean them up. After HTTP, MCP, or Qdrant smoke runs, check:

```sh
! lsof -i :8000
! lsof -i :6333
```

If a port remains bound, identify and clean up the process or container before finishing.

## Gotchas

- Do not use `scripts/qa_full.sh` as the docs-only proof for this plan.
- A successful script banner is not enough if a service remains bound afterward.
- Use `PYTHONDONTWRITEBYTECODE=1` for pytest commands to avoid bytecode artifacts under `app` and `tests`.

## Verification

Useful focused checks:

```sh
rg -q 'qa_http_contract.sh|qa_mcp_contract.sh|qa_qdrant_contract.sh' docs/testing.md
rg -q 'qa_full.sh.*context7-backend-reverse-engineer|not.*docs-only proof|docs-only' docs/testing.md
```

## Next

- Read [development](development.md) for local development commands.
- Read [deployment](deployment.md) for service startup and cleanup.
