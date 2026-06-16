# Open Context7 Backend Retrieval

Purpose: explain how Open Context7 Backend finds chunks for `/api/v2/context`.

Source of truth: `app/retrieval/lexical.py`, `app/retrieval/qdrant.py`, `app/embeddings.py`, `app/rerank.py`, `app/settings.py`, and the retrieval tests under `tests/`.

## Modes

`DOCS_RETRIEVAL_MODE=lexical` is the default local mode. It reads the local chunk store, tokenizes the query and chunk content with a simple alphanumeric tokenizer, filters chunks by `library_id` and `version`, optionally filters by chunk `kind`, and ranks matches by overlap score. Ties are stable: `source_path`, `heading`, and `chunk_index`.

`DOCS_RETRIEVAL_MODE=qdrant` uses Qdrant through `app/retrieval/qdrant.py`. Ingest replaces the selected library/version in Qdrant and the context route queries Qdrant with the same library/version constraints.

## Qdrant Collection And Payload

Qdrant retrieval uses one shared `docs` collection for all indexed libraries. The adapter creates keyword payload indexes for `library_id`, `version`, `kind`, and `source_path`.

Each point payload stores the chunk ID, `library_id`, `version`, `kind`, `source_path`, heading, chunk index, language, token count, content, and line numbers. Query filters always include `library_id` and `version`; they can also include `kind` and `source_path` when the caller supplies those constraints.

## Deterministic Embeddings

The current embedding implementation is deterministic. `app/embeddings.py` hashes text with SHA-256 and expands the digest into a fixed-size vector. `DOCS_EMBEDDING_MODE=deterministic` documents the current supported behavior; no remote embedding provider is wired in this backend.

## Token Budget

`DOCS_MAX_CONTEXT_TOKENS` is parsed by settings, but the current context route still passes a fixed 5000-token budget into retrieval. Local lexical retrieval keeps adding ranked chunks until the next chunk would exceed the budget it receives, after at least one chunk has already been selected. This means a single best chunk can be returned even when it is larger than that route budget.

Qdrant query size is currently controlled by the adapter request limit. Treat the configured context budget as a parsed setting until route behavior is wired to use it.

## Reranker Limitation

`DOCS_RERANKER_ENABLED` is parsed by settings, but `app/rerank.py` currently performs a pass-through: it returns chunks in the order it received them for both enabled and disabled states. Treat reranking as a configuration placeholder until the implementation changes.

## Gotchas

- Re-ingesting a library/version in Qdrant deletes that library/version before upserting replacement chunks.
- Local lexical retrieval only scores chunks with at least one token overlap with the query.
- Qdrant payload indexes are created for filter fields, not for every payload field.
- Retrieval docs should not imply LLM snippet extraction; ingestion and retrieval are deterministic in this repository.

## Verification

Useful focused checks:

```sh
PYTHONDONTWRITEBYTECODE=1 uv run pytest -q -p no:cacheprovider tests/test_retrieval_lexical.py tests/test_qdrant_adapter.py tests/test_embeddings_rerank.py
rg -q 'shared.*docs.*collection|payload indexes|library_id|version|kind|source_path' docs/retrieval.md
```

## Next

- Read [ingestion](ingestion.md) for how chunks are created.
- Read [API](api.md) for how chunks are formatted as snippets.
