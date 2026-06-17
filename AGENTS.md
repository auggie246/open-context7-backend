# Repository Instructions

This file governs the whole repository. Keep it minimal and update it only with durable facts that help future agent work.

## Project Shape

- Python 3.12+ FastAPI backend for a Context7-compatible docs API.
- Main package entrypoint: `context7-backend = "app.cli:main"`.
- Catalog metadata lives in `libraries/*.yaml`; keep those files as the source of truth for library IDs, versions, and source paths.
- The Markdown/MDX ingestion path is deterministic by design. Do not introduce LLM extraction into parsing or indexing.

## Common Commands

- Quality gate: `scripts/verify_code_quality.sh`
- Full QA gate: `scripts/qa_full.sh`
- Fast tests: `PYTHONDONTWRITEBYTECODE=1 uv run pytest -q -p no:cacheprovider`
- Lint: `uv run ruff check app tests`
- Type check: `uv run basedpyright app tests`
- Example ingest: `uv run context7-backend ingest --library /internal/platform --version main --source-dir examples/platform-docs`
- Run API locally: `uv run uvicorn app.main:app --host 127.0.0.1 --port 8000`
- MCP client env: `CONTEXT7_API_URL=http://localhost:8000/api`

## QA Scripts

- HTTP contract: `scripts/qa_http_contract.sh`
- Qdrant contract: `scripts/qa_qdrant_contract.sh`
- MCP contract: `scripts/qa_mcp_contract.sh`
- Plan compliance: `scripts/verify_plan_compliance.sh`
- Scope fidelity: `scripts/verify_scope_fidelity.sh`

## Footguns

- `src/context7--upstash-context7-mcp-3.2.1` is ignored, vendored reference material. Do not edit or commit it.
- `.omo/` and `.omc/` are local agent evidence/session state. Do not commit them unless explicitly requested.
- Avoid generating or committing `__pycache__` and `.pyc`; QA scripts set `PYTHONDONTWRITEBYTECODE=1` and check for bytecode under `app` and `tests`.
- Ingestion must reject symlink escapes and enforce resolved-path containment. Keep `tests/test_ingest_cli.py::test_ingest_cli_rejects_symlink_escape` passing.
- Auth must use constant-time comparison with `secrets.compare_digest` across configured API keys; do not replace it with plain membership checks.
- The stock `@modelcontextprotocol/sdk` 1.29 stdio transport uses newline-delimited JSON, not `Content-Length` framing.
- Docker Compose binds `docs-api` and Qdrant to `127.0.0.1` and defaults `DOCS_API_KEYS` to `dev-local-secret`.
- `/healthz` is intentionally unauthenticated; `/api/v2/*` requires bearer auth when API keys are configured.
- Qdrant retrieval uses the shared `docs` collection and payload indexes for `library_id`, `version`, `kind`, and `source_path`.
- If Compose or QA starts services, clean up and check ports `8000` and `6333` before finishing.

## Scope Boundaries

- Do not add a web UI, OIDC/team auth, HTML/sitemap crawling, Kubernetes deployment, LLM snippet extraction, or vendored Context7 source edits for the current v1 backend.
- Prefer strict typing and existing project patterns. `pyproject.toml` enables strict BasedPyright and Ruff for `app` and `tests`.


<!-- headroom:rtk-instructions -->
# RTK (Rust Token Killer) - Token-Optimized Commands

When running shell commands, **always prefix with `rtk`**. This reduces context
usage by 60-90% with zero behavior change. If rtk has no filter for a command,
it passes through unchanged — so it is always safe to use.

## Key Commands
```bash
# Git (59-80% savings)
rtk git status          rtk git diff            rtk git log

# Files & Search (60-75% savings)
rtk ls <path>           rtk read <file>         rtk grep <pattern>
rtk find <pattern>      rtk diff <file>

# Test (90-99% savings) — shows failures only
rtk pytest tests/       rtk cargo test          rtk test <cmd>

# Build & Lint (80-90% savings) — shows errors only
rtk tsc                 rtk lint                rtk cargo build
rtk prettier --check    rtk mypy                rtk ruff check

# Analysis (70-90% savings)
rtk err <cmd>           rtk log <file>          rtk json <file>
rtk summary <cmd>       rtk deps                rtk env

# GitHub (26-87% savings)
rtk gh pr view <n>      rtk gh run list         rtk gh issue list

# Infrastructure (85% savings)
rtk docker ps           rtk kubectl get         rtk docker logs <c>

# Package managers (70-90% savings)
rtk pip list            rtk pnpm install        rtk npm run <script>
```

## Rules
- In command chains, prefix each segment: `rtk git add . && rtk git commit -m "msg"`
- For debugging, use raw command without rtk prefix
- `rtk proxy <cmd>` runs command without filtering but tracks usage
<!-- /headroom:rtk-instructions -->
