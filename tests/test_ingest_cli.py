from pathlib import Path

from app.cli import cli
from app.store import load_chunks
from typer.testing import CliRunner


def test_ingest_cli_when_source_dir_given_persists_chunks() -> None:
    runner = CliRunner()
    Path(".omo/local-store/chunks.json").unlink(missing_ok=True)

    result = runner.invoke(
        cli,
        [
            "ingest",
            "--library",
            "/internal/platform",
            "--version",
            "main",
            "--source-dir",
            "tests/fixtures/docs",
        ],
    )

    chunks = load_chunks(Path(".omo/local-store/chunks.json"))

    assert result.exit_code == 0
    assert "ingested 6 chunks" in result.stdout
    assert [chunk.library_id for chunk in chunks] == ["/internal/platform"] * 6


def test_ingest_cli_applies_catalog_excludes_and_replaces_orphans(tmp_path: Path) -> None:
    runner = CliRunner()
    store_path = Path(".omo/local-store/chunks.json")
    store_path.unlink(missing_ok=True)
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    kept = docs_dir / "guide.md"
    draft = docs_dir / "draft-hidden.md"
    _ = kept.write_text("# Guide\n\nvaluesFrom kept\n", encoding="utf-8")
    _ = draft.write_text("# Draft\n\nvaluesFrom draft\n", encoding="utf-8")

    first_result = runner.invoke(
        cli,
        [
            "ingest",
            "--library",
            "/internal/platform",
            "--version",
            "main",
            "--source-dir",
            str(docs_dir),
        ],
    )

    chunks = load_chunks(store_path)
    assert first_result.exit_code == 0
    assert [chunk.source_path for chunk in chunks] == [str(kept)]
    assert "draft" not in chunks[0].content

    _ = kept.write_text("# Guide\n\nvaluesFrom changed\n", encoding="utf-8")
    second_result = runner.invoke(
        cli,
        [
            "ingest",
            "--library",
            "/internal/platform",
            "--version",
            "main",
            "--source-dir",
            str(docs_dir),
        ],
    )

    replaced = load_chunks(store_path)
    assert second_result.exit_code == 0
    assert len(replaced) == 1
    assert replaced[0].content == "valuesFrom changed"


def test_ingest_cli_rejects_symlink_escape(tmp_path: Path) -> None:
    runner = CliRunner()
    store_path = Path(".omo/local-store/chunks.json")
    store_path.unlink(missing_ok=True)
    docs_dir = tmp_path / "docs"
    outside_dir = tmp_path / "outside"
    docs_dir.mkdir()
    outside_dir.mkdir()
    outside_doc = outside_dir / "secret.md"
    escaped_link = docs_dir / "linked.md"
    _ = outside_doc.write_text("# Secret\n\nvaluesFrom secret\n", encoding="utf-8")
    escaped_link.symlink_to(outside_doc)

    result = runner.invoke(
        cli,
        [
            "ingest",
            "--library",
            "/internal/platform",
            "--version",
            "main",
            "--source-dir",
            str(docs_dir),
        ],
    )

    assert result.exit_code != 0
    assert "matched file escapes source directory" in result.output
    assert not store_path.exists()
