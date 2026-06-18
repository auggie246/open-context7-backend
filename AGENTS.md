# PROJECT KNOWLEDGE BASE

**Generated:** 2026-06-18
**Commit:** 5e7aeaf
**Branch:** main

## OVERVIEW

Python 3.12+ FastAPI backend that serves a Context7-compatible documentation API and an ingest CLI. Markdown/MDX ingestion, catalog loading, local lexical retrieval, and Qdrant retrieval are deterministic by design.

## STRUCTURE

```text
open-context7-backend/
├── app/                         # FastAPI app, CLI, ingest, retrieval, auth, formatters
├── tests/                       # Behavior-surface pytest suite and fixtures
├── docs/                        # User docs pinned by tests/test_docs_contract.py
├── scripts/                     # QA, contract, and scope validation scripts
├── libraries/                   # Source-of-truth catalog YAML
├── examples/platform-docs/      # Minimal ingest sample corpus
├── data/sources/fastapi/        # Larger local source corpus
├── charts/open-context7-backend/ # Helm chart released from .github workflow
└── src/context7--upstash-context7-mcp-3.2.1/ # Ignored vendored reference
```

## WHERE TO LOOK

| Task | Location | Notes |
| --- | --- | --- |
| HTTP app boot | `app/main.py` | `create_app()`, `/healthz`, router wiring |
| API routes | `app/routes.py` | `/api/v2/libs/search`, `/api/v2/context` |
| CLI ingest | `app/cli.py` | `context7-backend ingest` entrypoint |
| Parser behavior | `app/ingest/parser.py` | deterministic Markdown/MDX chunking |
| Local storage | `app/store.py` | `.local-store/chunks.json` replacement behavior |
| Qdrant storage | `app/retrieval/qdrant.py` | shared `docs` collection and payload indexes |
| Catalog metadata | `libraries/*.yaml` | IDs, versions, include/exclude globs |
| Contract docs | `docs/` | README/doc links and markers are tested |
| QA gates | `scripts/` | quality, HTTP, MCP, Qdrant, scope checks |
| Deployment | `Dockerfile`, `docker-compose.yml`, `charts/open-context7-backend/` | compose and chart contracts are tested/released |

## CODE MAP

| Symbol | Type | Location | Refs | Role |
| --- | --- | --- | --- | --- |
| `create_app` | function | `app/main.py` | tests, uvicorn | builds FastAPI app and registers auth/router |
| `healthz` | route | `app/main.py` | tests, compose healthcheck | intentionally unauthenticated readiness |
| `router` | APIRouter | `app/routes.py` | `create_app` | applies auth dependency to `/api/v2/*` |
| `search_libraries` | route | `app/routes.py` | API tests, MCP flow | Context7 library search response |
| `get_context` | route | `app/routes.py` | API/e2e tests, MCP flow | text/JSON context retrieval |
| `require_bearer_auth` | dependency | `app/auth.py` | router, auth tests | constant-time bearer-token validation |
| `ingest` | CLI command | `app/cli.py` | Typer, e2e, QA scripts | parse docs, replace local/Qdrant chunks |
| `parse_document` | function | `app/ingest/parser.py` | CLI, parser tests | deterministic MD/MDX chunk extraction |
| `save_chunks` | function | `app/store.py` | CLI, tests | replace one library/version without touching others |
| `LexicalRetriever` | class | `app/retrieval/lexical.py` | routes/tests | local deterministic retrieval |
| `QdrantAdapter` | class | `app/retrieval/qdrant.py` | CLI/routes/tests | Qdrant collection, indexes, upsert/query |
| `load_catalog` | function | `app/catalog.py` | routes/CLI/tests | YAML catalog normalization and validation |

## CONVENTIONS

- Run shell commands with `rtk` prefix. Use `rtk proxy <cmd>` when `rtk` cannot handle compound predicates or shell features.
- Package entrypoint is `context7-backend = "app.cli:main"`; keep app package at `app/`, not under `src/`.
- Strict checks cover only `app` and `tests`: Ruff `select = ["ALL"]`, BasedPyright `typeCheckingMode = "all"`.
- Catalog metadata lives in `libraries/*.yaml`; keep it the source of truth for library IDs, versions, source paths, aliases, include/exclude globs.
- Ingestion and retrieval are deterministic. Do not add LLM extraction, summarization, semantic rewriting, or generated snippet extraction to parsing/indexing.
- Use `PYTHONDONTWRITEBYTECODE=1` for pytest/QA, and avoid committed `__pycache__` or `.pyc` under `app` and `tests`.

## ANTI-PATTERNS

- Do not edit or commit `src/context7--upstash-context7-mcp-3.2.1`; it is vendored upstream reference material.
- Do not commit `.omo/`, `.omc/`, `.local-store/`, `.pytest_cache/`, `.ruff_cache/`, or bytecode artifacts unless explicitly requested.
- Do not replace `secrets.compare_digest` with plain membership checks for API keys.
- Do not make `/healthz` authenticated. `/api/v2/*` remains bearer-protected when API keys are configured.
- Do not add web UI, OIDC/team auth, HTML/sitemap crawling, Kubernetes deployment, LLM snippet extraction, or vendored Context7 source edits for the current v1 backend.
- Do not assume MCP stdio uses `Content-Length`; stock `@modelcontextprotocol/sdk` 1.29 stdio transport is newline-delimited JSON.

## COMMANDS

```bash
rtk scripts/verify_code_quality.sh
rtk scripts/qa_full.sh
PYTHONDONTWRITEBYTECODE=1 rtk uv run pytest -q -p no:cacheprovider
rtk uv run ruff check app tests
rtk uv run basedpyright app tests
rtk uv run context7-backend ingest --library /internal/platform --version main --source-dir examples/platform-docs
rtk uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
CONTEXT7_API_URL=http://localhost:8000/api rtk node scripts/qa_mcp_contract.mjs
```

## NOTES

- Docker Compose binds docs API to `127.0.0.1:8000` and Qdrant to `127.0.0.1:6333`; default `DOCS_API_KEYS` is `dev-local-secret`.
- Qdrant retrieval uses shared collection `docs` and payload indexes for `library_id`, `version`, `kind`, and `source_path`.
- If Compose or QA starts services, clean up and check ports `8000` and `6333` before finishing.
- `plans/self-service-ingestion.md` is currently untracked; do not treat it as committed project contract without checking git status.
