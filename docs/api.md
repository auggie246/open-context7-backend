# Open Context7 Backend API

Purpose: document the current local HTTP API implemented by `app/main.py`, `app/routes.py`, `app/models.py`, and `app/formatters.py`.

Base URL for local development:

```text
http://127.0.0.1:8000
```

Run locally:

```bash
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Auth Behavior

`/healthz` is not part of the `/api/v2` router and is intentionally unauthenticated.

`/api/v2/*` routes use the bearer auth dependency from `app/auth.py`. When `DOCS_API_KEYS` is empty or unset, auth is disabled. When `DOCS_API_KEYS` contains one or more keys, clients must send:

```http
Authorization: Bearer <key>
```

Missing, malformed, or invalid bearer tokens return `401` with:

```json
{"error":"unauthorized","message":"Bearer token required"}
```

or:

```json
{"error":"unauthorized","message":"Invalid bearer token"}
```

The auth implementation compares configured keys with `secrets.compare_digest`. The API does not emit `X-Context7-Auth-Prompt`.

## `GET /healthz`

Health check for the FastAPI process.

Required params: none.

Auth: none.

Response: JSON `HealthResponse` from `app/models.py`.

Example:

```bash
curl -sS http://127.0.0.1:8000/healthz
```

Example shape:

```json
{
  "status": "ok",
  "service": "open-context7-backend",
  "checked_at": "2026-06-16T00:00:00Z"
}
```

## `GET /api/v2/libs/search`

Search local catalog entries from `libraries/*.yaml`.

Source behavior: `app/routes.py` loads catalog files, ranks them with `rank_catalogs()`, converts matches to the `Library` model, and returns `SearchResponse`.

Required query params:

- `query`: non-empty string, max 500 characters.
- `libraryName`: non-empty string, max 500 characters.

Optional query params:

- `fast`: `"true"` or `"false"`, default `"false"`. The current implementation accepts it but does not change ranking.

Auth: follows `/api/v2/*` behavior. Bearer auth is required only when `DOCS_API_KEYS` is configured.

Response mode: JSON only.

Response fields include:

- `results`: list of libraries.
- `searchFilterApplied`: currently `false`.
- Per-library fields such as `id`, `title`, `description`, `branch`, `lastUpdateDate`, `state`, `totalTokens`, `totalSnippets`, `trustScore`, `benchmarkScore`, and `versions`.

Example:

```bash
curl -sS \
  'http://127.0.0.1:8000/api/v2/libs/search?query=helm%20valuesFrom&libraryName=platform&fast=true'
```

With auth enabled:

```bash
curl -sS \
  -H 'Authorization: Bearer dev-local-secret' \
  'http://127.0.0.1:8000/api/v2/libs/search?query=helm%20valuesFrom&libraryName=platform'
```

Example shape:

```json
{
  "results": [
    {
      "id": "/internal/platform",
      "title": "Internal Platform",
      "description": "Example platform documentation",
      "branch": "main",
      "lastUpdateDate": "2026-01-01",
      "state": "finalized",
      "totalTokens": 0,
      "totalSnippets": 3,
      "trustScore": 10,
      "benchmarkScore": 95,
      "versions": ["main"]
    }
  ],
  "searchFilterApplied": false
}
```

Missing required params return FastAPI validation errors with status `422`.

## `GET /api/v2/context`

Retrieve snippets for a library and query.

Source behavior: `app/routes.py` resolves `libraryId` through `app/catalog.py`, retrieves chunks through local lexical retrieval or Qdrant retrieval, and formats the result through `app/formatters.py`.

Required query params:

- `query`: non-empty string, max 500 characters.
- `libraryId`: non-empty string, max 500 characters.

Optional query params:

- `type`: `"txt"` or `"json"`, default `"txt"`.
- `fast`: `"true"` or `"false"`, default `"false"`. The current implementation accepts it but does not change retrieval.

Versioned library IDs:

- `/owner/name` uses the catalog version, or `main` when the catalog has no explicit version.
- `/owner/name/version` is accepted for catalog matching.
- `/owner/name@version` is accepted for catalog matching.

The requested version must match the catalog's own version or one of the catalog `versions` entries. Retrieval currently uses the catalog default version for the route lookup, not the version-qualified ID's requested version.

Auth: follows `/api/v2/*` behavior. Bearer auth is required only when `DOCS_API_KEYS` is configured.

### `type=txt`

`type=txt` is the default response mode and returns `text/plain`.

Example:

```bash
curl -sS \
  'http://127.0.0.1:8000/api/v2/context?libraryId=/internal/platform&query=valuesFrom'
```

Equivalent explicit mode:

```bash
curl -sS \
  'http://127.0.0.1:8000/api/v2/context?libraryId=/internal/platform&query=valuesFrom&type=txt'
```

Text snippets include `TITLE`, `DESCRIPTION`, `SOURCE`, `LANGUAGE`, and either `CODE` or `CONTENT` sections. When retrieval finds no relevant chunks, `app/formatters.py` returns:

```text
No relevant snippets found for this query.
```

### `type=json`

`type=json` returns JSON shaped by `ContextResponse` in `app/models.py`.

Example:

```bash
curl -sS \
  'http://127.0.0.1:8000/api/v2/context?libraryId=/internal/platform@main&query=valuesFrom&type=json'
```

With auth enabled:

```bash
curl -sS \
  -H 'Authorization: Bearer dev-local-secret' \
  'http://127.0.0.1:8000/api/v2/context?libraryId=/internal/platform/main&query=valuesFrom&type=json'
```

Example shape:

```json
{
  "codeSnippets": [
    {
      "codeTitle": "Install",
      "codeDescription": "Install",
      "codeLanguage": "bash",
      "codeTokens": 4,
      "codeId": "guide.mdx#L1",
      "pageTitle": "Install",
      "codeList": [
        {
          "language": "bash",
          "code": "helm valuesFrom"
        }
      ],
      "isDynamic": null,
      "sourceFile": null
    }
  ],
  "infoSnippets": []
}
```

### Context Errors

Unknown libraries return `404`:

```json
{"error":"not_found","message":"Library not found"}
```

Missing required params return FastAPI validation errors with status `422`.

Invalid enum values, such as `type=html` or `fast=yes`, also return validation errors with status `422`.

Invalid bearer tokens return `401` when API keys are configured.

## Gotchas

- `/api/v2/context` returns snippets from ingested chunks; catalog metadata alone is not enough.
- `fast` is accepted for Context7-compatible wire contract shape but does not currently change ranking.
- `type=txt` and `type=json` are the only response modes.

## Verification

Useful checks for this page:

```bash
test -s docs/api.md
rg -q '/healthz' docs/api.md
rg -q '/api/v2/libs/search' docs/api.md
rg -q '/api/v2/context' docs/api.md
rg -q 'type=json|type=txt|libraryId|libraryName|searchFilterApplied' docs/api.md
```

## Next

- Read [auth](auth.md) for bearer-token details.
- Read [retrieval](retrieval.md) for local lexical retrieval and Qdrant retrieval.
