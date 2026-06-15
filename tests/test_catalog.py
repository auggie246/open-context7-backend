import subprocess
import sys
from pathlib import Path

import pytest
from app.catalog import (
    CatalogValidationError,
    JsonValue,
    ParsedLibraryId,
    load_catalog,
    parse_library_id,
)
from pydantic import TypeAdapter

FIXTURE_DIR = Path("tests/fixtures/catalog")


def test_load_catalog_when_yaml_valid_returns_normalized_metadata() -> None:
    catalog = load_catalog(FIXTURE_DIR / "valid-platform.yaml")

    library = catalog.library

    assert library.id == "/internal/platform"
    assert library.base_id == "/internal/platform"
    assert library.version is None
    assert library.title == "Internal Platform"
    assert library.description == "Deployment and Helm documentation for the internal platform."
    assert library.aliases == ("platform", "helm values")
    assert library.versions == ("main", "v1.2.0")
    assert library.source.type == "dir"
    assert library.source.directory == Path("tests/fixtures/catalog/docs/platform")
    assert library.source.branch == "main"
    assert library.source.include == ("docs/**/*.md", "**/*.mdx")
    assert library.source.exclude == ("**/draft*", "**/CHANGELOG*")
    assert library.state.status == "finalized"
    assert library.state.total_snippets == 12
    assert library.state.last_update_date.isoformat() == "2026-06-01"


def test_load_catalog_when_library_id_invalid_raises_validation_error() -> None:
    with pytest.raises(CatalogValidationError, match="library id"):
        _ = load_catalog(FIXTURE_DIR / "invalid-id.yaml")


def test_parse_library_id_when_version_suffix_present_normalizes_base_id() -> None:
    slash_version = parse_library_id("/vercel/next.js/v14.3.0")
    at_version = parse_library_id("/vercel/next.js@v14.3.0")

    assert slash_version == ParsedLibraryId(
        raw="/vercel/next.js/v14.3.0",
        base_id="/vercel/next.js",
        version="v14.3.0",
        version_style="/",
    )
    assert at_version == ParsedLibraryId(
        raw="/vercel/next.js@v14.3.0",
        base_id="/vercel/next.js",
        version="v14.3.0",
        version_style="@",
    )


def test_module_execution_when_catalog_valid_prints_normalized_metadata() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "app.catalog", str(FIXTURE_DIR / "valid-platform.yaml")],
        check=True,
        capture_output=True,
        text=True,
    )

    metadata = TypeAdapter(dict[str, JsonValue]).validate_json(result.stdout)
    source = metadata["source"]
    state = metadata["state"]

    assert isinstance(source, dict)
    assert isinstance(state, dict)

    assert metadata["id"] == "/internal/platform"
    assert metadata["baseId"] == "/internal/platform"
    assert metadata["aliases"] == ["platform", "helm values"]
    assert source["directory"] == "tests/fixtures/catalog/docs/platform"
    assert state["status"] == "finalized"
