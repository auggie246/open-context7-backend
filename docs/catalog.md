# Open Context7 Backend Catalog

Purpose: document the catalog metadata used by Open Context7 Backend.

Source of truth: `libraries/*.yaml`, `app/catalog.py`, `app/cli.py`, and `tests/test_catalog.py`.

Catalog files live in `libraries/*.yaml` and are the source of truth for library IDs, human-facing metadata, versions, aliases, source paths, include and exclude patterns, and state fields.

## File Location

Each catalog entry is a YAML file under `libraries/*.yaml`. Current local examples include:

- `libraries/internal-platform.yaml`
- `libraries/example.yaml`

The ingest command uses these files when `--library` matches a catalog entry's base library ID. API search also reads this catalog metadata to return library titles, descriptions, aliases, versions, and state.

## Library IDs

Library IDs must match the local pattern enforced by `app/catalog.py`: `/owner/name`, optionally with a version suffix.

Supported forms:

- Base ID: `/internal/platform`
- Slash version: `/vercel/next.js/v14.3.0`
- At-sign version: `/vercel/next.js@v14.3.0`

Both versioned forms normalize to the same base ID, such as `/vercel/next.js`, with the version recorded separately. Invalid forms raise `CatalogValidationError` during catalog loading or parsing.

## YAML Fields

A catalog file contains:

```yaml
id: /internal/platform
title: Internal Platform
description: Deployment and Helm documentation for the internal platform.
aliases:
  - platform
versions:
  - main
source:
  type: dir
  directory: examples/platform-docs
  branch: main
  include:
    - "**/*.md"
    - "**/*.mdx"
  exclude:
    - "**/draft*"
state:
  status: finalized
  totalSnippets: 2
  lastUpdateDate: 2026-06-15
```

`id`, `title`, `description`, `source`, and `state` are required by the model. `aliases`, `versions`, `source.branch`, `source.include`, and `source.exclude` have defaults or may be empty depending on the field.

## Source Configuration

`source.type` is currently `dir`. `source.directory` points to the local documentation directory for the library, and `source.branch` records the branch label associated with that source.

`source.include` and `source.exclude` are glob patterns used by ingestion:

- `include` defaults to `**/*.md` and `**/*.mdx`.
- `exclude` defaults to an empty list.
- Excludes are applied to relative paths after include matches.

The catalog source directory is metadata; the CLI still receives `--source-dir` explicitly for the ingest run. When the library base ID matches a catalog file, the CLI uses that catalog entry's include and exclude patterns with the provided source directory.

## Versions And Aliases

`versions` lists the versions advertised for a library, such as `main` or `v1.2.0`. The request and ingest paths also accept explicit version labels. A version suffix in a library ID is parsed into a base ID and version for lookup.

`aliases` are alternate search terms for a library. They are loaded with the catalog and exposed in normalized metadata.

## State Fields

`state` records catalog status and counts:

- `status`: one of `finalized`, `initial`, `processing`, `error`, or `delete`.
- `totalSnippets`: integer snippet count.
- `lastUpdateDate`: date field serialized as ISO format.

These fields describe catalog metadata and search output. They do not replace ingestion; the actual searchable chunks still come from parsing and storing source files.

## Validation Behavior

`load_catalog` reads YAML with `yaml.safe_load`, validates it with Pydantic models, parses the ID, and raises `CatalogValidationError` for invalid files or invalid library IDs. The module can also be executed directly to print normalized catalog metadata as JSON:

```bash
python -m app.catalog libraries/internal-platform.yaml
```

Useful checks:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run pytest -q -p no:cacheprovider tests/test_catalog.py
```

## Gotchas

- Catalog metadata describes libraries, but searchable chunks still come from ingestion.
- A versioned request still needs a base catalog entry such as `/internal/platform`.
- Include and exclude globs are consumed by ingestion with the provided `--source-dir`; they are not a crawler.

## Next

- Read [ingestion](ingestion.md) for how catalog entries become chunks.
- Read [API](api.md) for how catalog metadata appears in `/api/v2/libs/search`.
