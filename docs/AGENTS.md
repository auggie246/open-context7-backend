# DOCS KNOWLEDGE BASE

**Generated:** 2026-06-18

## OVERVIEW

User-facing documentation for the local backend; docs are contract-tested against README links and source-of-truth markers.

## WHERE TO LOOK

| Topic | File | Source markers |
| --- | --- | --- |
| API | `api.md` | `app/routes.py`, formatters, models |
| Auth | `auth.md` | `app/auth.py`, `/healthz`, `secrets.compare_digest` |
| Catalog | `catalog.md` | `libraries/*.yaml`, `app/catalog.py` |
| Configuration | `configuration.md` | `.env.example`, `app/settings.py`, `DOCS_API_KEYS` |
| Deployment | `deployment.md` | `Dockerfile`, `docker-compose.yml`, loopback ports |
| Development | `development.md` | `pyproject.toml`, `app/`, `tests/`, QA commands |
| Ingestion | `ingestion.md` | `app/cli.py`, `app/ingest/parser.py`, catalog globs |
| Retrieval | `retrieval.md` | lexical/Qdrant modules and payload indexes |
| Testing | `testing.md` | QA scripts and cleanup checks |
| Troubleshooting | `troubleshooting.md` | 401, Qdrant, symlink issues |

## CONVENTIONS

- Keep every README docs link resolvable; `tests/test_docs_contract.py` checks this.
- Each page should name its source-of-truth files and durable contract strings.
- Document observed behavior only. Do not claim planned features such as OIDC/team auth, web UI, crawling, or Kubernetes deployment.
- Use examples that match current commands, ports, auth defaults, and response formats.
- For docs-only edits, run the docs contract test and any direct marker checks relevant to the page.

## ANTI-PATTERNS

- Do not imply ingestion or retrieval uses LLM snippet extraction.
- Do not document `X-Context7-Auth-Prompt`; this backend intentionally does not emit it.
- Do not present Compose’s `dev-local-secret` as production-safe.
- Do not describe vendored Context7 source as editable project code.

## COMMANDS

```bash
PYTHONDONTWRITEBYTECODE=1 rtk uv run pytest -q -p no:cacheprovider tests/test_docs_contract.py
rtk grep -n "docs/" README.md docs/*.md
```
