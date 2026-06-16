# Open Context7 Backend Architecture

Purpose: explain the request and data flow for the local FastAPI backend from catalog metadata through ingestion, storage, retrieval, formatting, and HTTP routes.

Local source of truth:
- `app/main.py` creates the FastAPI app, registers auth error handling, includes `app/routes.py`, and mounts `/healthz`.
- `app/routes.py` owns the `/api/v2` HTTP contract and chooses local lexical retrieval or Qdrant retrieval.
- `app/catalog.py`, `libraries/*.yaml`, `app/cli.py`, `app/store.py`, and `app/retrieval` define the catalog, ingest, store, and retrieval behavior.
- `app/formatters.py` converts retrieved chunks into `type=txt` or `type=json` responses.

## Component Flow

The backend is intentionally small and deterministic:

1. Catalog metadata starts in `libraries/*.yaml`. `app/catalog.py` validates each YAML file, parses library IDs, and exposes the base ID, optional version, aliases, versions, source directory, include/exclude globs, and state fields.
2. Ingestion runs through `context7-backend ingest`, implemented in `app/cli.py`. The CLI finds the matching catalog, resolves the source directory, applies catalog include/exclude globs, parses Markdown/MDX files, and materializes chunks for a specific `library_id` and `version`.
3. The local store is `.omo/local-store/chunks.json`, written by `app/store.py`. Saving chunks replaces the previous chunks for the same library/version and keeps the merged store sorted by library ID, version, source path, and chunk index.
4. Retrieval happens in `app/retrieval`. `app/routes.py` calls `retrieve_chunks()`, which selects the backend from `DOCS_RETRIEVAL_MODE`.
5. Formatting happens in `app/formatters.py`. Text mode emits Context7-style snippet blocks. JSON mode splits retrieved chunks into `codeSnippets` and `infoSnippets`.
6. HTTP responses return from the FastAPI route handlers in `app/routes.py`, with models defined in `app/models.py`.

The path is:

```text
libraries/*.yaml
  -> app/catalog.py
  -> app/cli.py ingest
  -> app/store.py or app/retrieval/qdrant.py
  -> app/retrieval/lexical.py or app/retrieval/qdrant.py
  -> app/formatters.py
  -> app/routes.py
  -> app/main.py FastAPI app
```

## Request Flow

`app/main.py` builds the `Open Context7 Backend` FastAPI application. It registers the auth exception handler from `app/auth.py`, includes the router from `app/routes.py`, and adds `/healthz`.

The API router in `app/routes.py` is mounted at `/api/v2` and has a router-level `require_bearer_auth` dependency. That means `/healthz` is outside the protected router, while `/api/v2/libs/search` and `/api/v2/context` are protected when `DOCS_API_KEYS` is configured.

`/api/v2/libs/search` loads all catalog files under `libraries/`, ranks catalog entries against `query` and `libraryName`, and returns the `SearchResponse` shape from `app/models.py`.

`/api/v2/context` parses `libraryId`, resolves it to a local catalog, accepts and validates version-qualified IDs, retrieves chunks for the catalog base ID and catalog default version, then returns either `PlainTextResponse` for `type=txt` or a `ContextResponse` model for `type=json`.

## Catalog And Versioned IDs

`app/catalog.py` accepts these library ID forms:

- `/owner/name`
- `/owner/name/version`
- `/owner/name@version`

The route uses the parsed base ID to find the catalog. If a version is provided, it must match the catalog's own version or one of its declared `versions`. If no version is provided, `app/routes.py` falls back to the catalog version or `main`.

## Ingestion Flow

The ingestion command is:

```bash
uv run context7-backend ingest --library /internal/platform --version main --source-dir examples/platform-docs
```

`app/cli.py` uses catalog include/exclude patterns when the catalog exists, otherwise it defaults to Markdown and MDX files. It resolves the source root and rejects matched files whose resolved path escapes the source directory.

Parsed chunks are saved locally through `app/store.py`. If `DOCS_RETRIEVAL_MODE=qdrant`, the same command also writes the chunks into Qdrant through `app/retrieval/qdrant.py`.

## Local Lexical Retrieval

Local lexical retrieval is the default mode. `app/routes.py` calls `LexicalRetriever(load_chunks()).search(...)` when `DOCS_RETRIEVAL_MODE` is `lexical`.

`app/retrieval/lexical.py` tokenizes the query and chunk content, filters by library ID and version, optionally filters by chunk kind, ranks by token overlap, and applies a token budget. Sorting is deterministic: score descending, then source path, heading, and chunk index.

This mode uses the local `.omo/local-store/chunks.json` store and does not require Qdrant.

## Qdrant Retrieval

Qdrant retrieval is selected with `DOCS_RETRIEVAL_MODE=qdrant`. In that mode, `app/routes.py` creates a `QdrantAdapter` with `QdrantClient(url=settings.qdrant_url, check_compatibility=False)` and queries it with library ID, version, query, and a limit.

`app/retrieval/qdrant.py` uses the shared collection named `docs`. It creates payload indexes for `library_id`, `version`, `kind`, and `source_path`, embeds content with the deterministic embedding client by default, and filters queries by library ID and version, with optional kind and source path filters.

## Formatters

`app/formatters.py` is the final translation layer before the route response:

- `format_text_context()` returns text/plain content. No matches become `No relevant snippets found for this query.`
- `format_json_context()` returns JSON-compatible `ContextResponse` data with code chunks under `codeSnippets` and prose chunks under `infoSnippets`.

## Constraints And Gotchas

- Catalog metadata in `libraries/*.yaml` is the source of truth for documented library metadata.
- Markdown/MDX ingestion is deterministic. Do not describe LLM extraction as part of parsing or indexing.
- `/healthz` is intentionally unauthenticated.
- `/api/v2/*` is protected only when `DOCS_API_KEYS` is configured.
- The vendored `src/context7--upstash-context7-mcp-3.2.1` tree is reference material only and is not part of the implementation flow documented here.

## Verification

Useful checks for this page:

```bash
test -s docs/architecture.md
rg -q 'app/routes.py|app/main.py|app/formatters.py|app/retrieval' docs/architecture.md
```

## Next

- Read [API](api.md) for endpoint details.
- Read [ingestion](ingestion.md) and [retrieval](retrieval.md) for the data path.
