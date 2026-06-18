# CATALOG KNOWLEDGE BASE

**Generated:** 2026-06-18

## OVERVIEW

Catalog YAML files are the source of truth for library IDs, versions, aliases, source paths, include/exclude globs, and display metadata.

## WHERE TO LOOK

| Task | Location | Notes |
| --- | --- | --- |
| Catalog schema behavior | `../app/catalog.py` | normalization, ID parsing, validation |
| Catalog tests | `../tests/test_catalog.py` | valid/invalid fixtures and CLI output |
| Ingest selection | `../app/cli.py` | include/exclude globs and source-dir containment |
| Docs | `../docs/catalog.md`, `../docs/ingestion.md` | user-facing catalog and ingest contracts |

## CONVENTIONS

- Library IDs are slash-prefixed Context7-style IDs, for example `/internal/platform`.
- Keep version labels explicit and aligned with source paths used by ingest examples and tests.
- Include/exclude globs drive ingestion; changing them can remove orphan chunks on re-ingest.
- Keep YAML deterministic and human-readable. Avoid generated churn in ordering or comments.
- Update docs and tests when catalog fields become required or change semantics.

## ANTI-PATTERNS

- Do not move catalog authority into README, docs text, `.local-store`, or source corpus directories.
- Do not point catalog source paths outside intended local documentation roots.
- Do not use catalog files to describe unsupported crawlers or remote fetch behavior.

## COMMANDS

```bash
PYTHONDONTWRITEBYTECODE=1 rtk uv run pytest -q -p no:cacheprovider tests/test_catalog.py tests/test_ingest_cli.py
rtk uv run context7-backend ingest --library /internal/platform --version main --source-dir examples/platform-docs
```
