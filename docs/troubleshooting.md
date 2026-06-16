# Open Context7 Backend Troubleshooting

Purpose: list common local failures for Open Context7 Backend and the first checks to run.

Source of truth: `app/catalog.py`, `app/cli.py`, `app/formatters.py`, `app/auth.py`, `app/retrieval/qdrant.py`, `docker-compose.yml`, `scripts/qa_http_contract.sh`, and `scripts/qa_qdrant_contract.sh`.

## Missing Catalog Results

Symptoms:

- `/api/v2/libs/search` does not return the expected library.
- `/api/v2/context` returns a not-found error for a library ID.

Checks:

```sh
ls libraries
rg -n '/internal/platform|aliases|versions|source' libraries/*.yaml
uv run context7-backend ingest --library /internal/platform --version main --source-dir examples/platform-docs
```

Catalog metadata lives in `libraries/*.yaml`. Confirm the requested ID, alias, version, source directory, and include/exclude globs are present there. Library IDs can include a version as `/owner/name/version` or `/owner/name@version`, but the base catalog still needs to exist.

## Empty Context Or No Matches

Symptoms:

- Text context returns `No relevant snippets found for this query.`
- JSON context returns empty `codeSnippets` and `infoSnippets`.

Checks:

```sh
test -s .local-store/chunks.json
rg -n 'valuesFrom|platform' examples/platform-docs .local-store/chunks.json
curl 'http://127.0.0.1:8000/api/v2/context?libraryId=/internal/platform&query=valuesFrom'
```

Common causes are stale or missing local chunks, a query that has no token overlap with stored content, the wrong version, or Qdrant retrieval pointing at an empty collection. Re-run ingest for the library/version before debugging retrieval ranking.

## Auth 401

Symptoms:

- `/api/v2/*` returns HTTP 401.
- Error body contains `unauthorized`.

Checks:

```sh
curl -i http://127.0.0.1:8000/healthz
curl -i 'http://127.0.0.1:8000/api/v2/libs/search?query=platform&libraryName=platform'
curl -i -H 'Authorization: Bearer dev-local-secret' \
  'http://127.0.0.1:8000/api/v2/libs/search?query=platform&libraryName=platform'
```

Auth is disabled only when `DOCS_API_KEYS` is empty. Docker Compose defaults `DOCS_API_KEYS` to `dev-local-secret`, so `/api/v2/*` needs `Authorization: Bearer dev-local-secret` unless the key is overridden. `/healthz` is intentionally unauthenticated.

## Qdrant Readiness

Symptoms:

- Qdrant retrieval returns no results after switching to `DOCS_RETRIEVAL_MODE=qdrant`.
- Ingest fails to write to Qdrant.
- The API starts before Qdrant is ready.

Checks:

```sh
curl -f http://127.0.0.1:6333/collections
DOCS_RETRIEVAL_MODE=qdrant uv run python -m app.retrieval.qdrant --smoke
DOCS_RETRIEVAL_MODE=qdrant uv run context7-backend ingest --library /internal/platform --version main --source-dir examples/platform-docs
```

`docker-compose.yml` starts Qdrant on `127.0.0.1:6333`. Qdrant retrieval uses the shared `docs` collection with payload indexes for `library_id`, `version`, `kind`, and `source_path`. Re-ingest after Qdrant is ready so the collection contains current chunks.

## Port Conflicts

Symptoms:

- `uvicorn` cannot bind port `8000`.
- Qdrant or Compose cannot bind port `6333`.
- QA scripts appear to start but calls hit an older local service.

Checks:

```sh
lsof -i :8000
lsof -i :6333
docker compose down
```

This repository expects local API traffic on `127.0.0.1:8000` and Qdrant on `127.0.0.1:6333`. Stop stale processes or containers before rerunning QA, then verify the ports are free.

## Stale Local Store

Symptoms:

- Old snippets appear after docs changed.
- A deleted file still appears in context results.
- Local lexical retrieval disagrees with the source directory.

Checks:

```sh
rm -f .local-store/chunks.json
uv run context7-backend ingest --library /internal/platform --version main --source-dir examples/platform-docs
```

`app/store.py` replaces chunks for the same library/version during ingest, but a stale store can still come from ingesting the wrong source directory, library, or version. Remove the local store and re-ingest the intended catalog entry.

## Symlink Escape Errors

Symptoms:

- Ingest fails with a symlink escape error.
- A matched Markdown or MDX file resolves outside the source directory.

Checks:

```sh
find examples/platform-docs -type l -ls
uv run context7-backend ingest --library /internal/platform --version main --source-dir examples/platform-docs
```

The ingest path resolves each matched file and rejects symlink escapes outside the resolved source root. This is intentional containment behavior. Move the target file inside the source tree or remove the symlink from the included paths.

## Malformed Inputs

Malformed library IDs, missing query parameters, unsupported versions, and bad authorization headers should fail through normal API errors rather than being treated as successful matches. Keep troubleshooting examples explicit: record the exact URL, status code, and environment variables used for the failing request.

## Verification

Useful focused checks:

```sh
rg -q '401|Qdrant|port|No relevant snippets|symlink' docs/troubleshooting.md
```

## Gotchas

- Check catalog metadata before debugging retrieval ranking.
- Check auth mode before treating a 401 as an API routing problem.
- Check stale local chunks or Qdrant state before changing source docs.

## Next

- Read [catalog](catalog.md) for library metadata checks.
- Read [deployment](deployment.md) for port and service cleanup.
