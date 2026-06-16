# Open Context7 Backend Ingestion

Purpose: document the local Markdown and MDX ingestion path for Open Context7 Backend.

Source of truth: `app/cli.py`, `app/ingest/parser.py`, `app/ingest/models.py`, `app/store.py`, `app/catalog.py`, `libraries/*.yaml`, and `tests/test_ingest_cli.py`.

## Command

Run ingestion with the package CLI:

```bash
uv run context7-backend ingest --library /internal/platform --version main --source-dir examples/platform-docs
```

`context7-backend ingest` requires:

- `--library`: the target library ID, such as `/internal/platform`.
- `--version`: the version label to attach to generated chunks. It defaults to `main`.
- `--source-dir`: the documentation directory to scan.

The command prints `ingested N chunks` after saving chunks. In local lexical retrieval the chunks are written to the local store. In Qdrant retrieval the same chunks are also sent through the Qdrant replacement path.

## Source Selection

`app/cli.py` resolves `--source-dir` with strict path resolution before scanning. When a matching catalog entry exists under `libraries/*.yaml`, ingestion uses that entry's `source.include` and `source.exclude` globs. Without a matching catalog entry it falls back to `**/*.md` and `**/*.mdx` and no excludes.

Include globs are evaluated from the resolved source root. Exclude globs are applied to each matched relative path, including common patterns such as `**/draft*`. Matched files must remain inside the resolved source root. A symlink that points outside the source directory is rejected with `matched file escapes source directory`, and no local store file is written for that failed run.

## Parser Behavior

Parsing is deterministic: the same Markdown or MDX input produces the same ordered chunk records. `app/ingest/parser.py` handles the current local format rules:

- YAML-style frontmatter at the start of a file is skipped.
- MDX `import` and `export` lines are skipped.
- JSX component blocks that start with an uppercase tag are skipped.
- Markdown headings become the current chunk heading.
- Prose chunks are split on headings, blank lines, fences, and skipped MDX blocks.
- Fenced code blocks are preserved as code chunks, including the opening and closing fence text.
- Fence languages such as `bash` or `ts` are captured when present.
- Token counts are deterministic counts of alphanumeric and underscore tokens.

This path is deterministic parsing and indexing. It does not perform generated extraction, summarization, or semantic rewriting.

## Chunk Identity

`app/ingest/models.py` turns parser chunks into stored document chunks. Stable chunk IDs are SHA-256 hashes over the library ID, version, source path, chunk index, and normalized chunk content. The stable chunk ID design means unchanged content at the same logical location keeps the same ID across repeated ingestion.

Each stored chunk includes the library ID, version, source path, heading, chunk index, language, kind (`code` or `prose`), token count, content, and source line range.

## Local Store And Replacement

The local store path is `.local-store/chunks.json`, defined in `app/store.py`. `save_chunks` materializes parsed chunks, loads any existing local chunks, removes existing chunks for the same `library_id` and `version`, and writes the merged result sorted by library ID, version, source path, and chunk index.

That replacement behavior intentionally removes orphan chunks for a library/version when a later ingest has fewer files or changed include/exclude patterns. Chunks for other libraries or versions remain in the local store.

## Verification

Useful checks:

```bash
uv run context7-backend ingest --library /internal/platform --version main --source-dir examples/platform-docs
PYTHONDONTWRITEBYTECODE=1 uv run pytest -q -p no:cacheprovider tests/test_parser.py tests/test_ingest_cli.py tests/test_ingest_repository.py
```

Important coverage includes deterministic parser output, fenced code preservation, catalog exclude handling, orphan replacement, and symlink escape rejection.

## Gotchas

- Ingestion is deterministic parsing and indexing, not LLM snippet extraction.
- A failed symlink containment check rejects the ingest run before writing local chunks.
- Re-ingesting a library/version replaces old chunks for that same library/version.

## Next

- Read [catalog](catalog.md) for `libraries/*.yaml` fields.
- Read [retrieval](retrieval.md) for how stored chunks become snippets.
