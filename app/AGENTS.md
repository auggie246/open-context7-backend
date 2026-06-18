# APP KNOWLEDGE BASE

**Generated:** 2026-06-18

## OVERVIEW

Runtime package for the FastAPI API, Typer ingest CLI, deterministic parser, local store, and retrieval adapters.

## WHERE TO LOOK

| Task | Location | Notes |
| --- | --- | --- |
| App factory | `main.py` | `create_app()`, `/healthz`, `app.state.settings` |
| Auth | `auth.py` | bearer dependency and 401 JSON handler |
| Settings | `settings.py` | `DOCS_` env parsing and retrieval mode |
| Catalog | `catalog.py` | YAML normalization and versioned ID parsing |
| Routes | `routes.py` | search/context response contracts |
| Formatting | `formatters.py` | text and JSON context wire shapes |
| Ingest CLI | `cli.py` | source selection, symlink containment, store/Qdrant replacement |
| Parser | `ingest/parser.py` | Markdown/MDX chunking rules |
| Retrieval | `retrieval/lexical.py`, `retrieval/qdrant.py` | local scoring and Qdrant adapter |

## CONVENTIONS

- Keep public behavior pinned by route tests and formatter tests; routes should return the Context7-shaped models from `models.py`.
- Prefer small typed helpers over route-level branching. BasedPyright is strict for this package.
- Preserve Pydantic v2 models and settings patterns already used in `models.py` and `settings.py`.
- Parser output must be stable across runs: source path, heading, chunk index, kind, token count, and line ranges should not depend on filesystem order or external services.
- CLI source selection must resolve paths strictly and reject symlink escapes before writing local store or Qdrant data.

## ANTI-PATTERNS

- Do not add LLM calls, nondeterministic extraction, or semantic rewriting in `ingest/`.
- Do not weaken `/api/v2/*` auth by moving the dependency off the router.
- Do not change `/healthz` into a protected API route.
- Do not replace local store replacement semantics with append-only behavior.
- Do not create Qdrant collections per library/version; current contract is one shared `docs` collection.

## VERIFICATION

```bash
PYTHONDONTWRITEBYTECODE=1 rtk uv run pytest -q -p no:cacheprovider tests/test_api_search.py tests/test_api_context.py tests/test_ingest_cli.py tests/test_retrieval_lexical.py tests/test_qdrant_adapter.py
rtk uv run ruff check app tests
rtk uv run basedpyright app tests
```
