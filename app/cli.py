from fnmatch import fnmatch
from pathlib import Path
from typing import Annotated

import typer
from qdrant_client import QdrantClient

from app.catalog import Catalog, load_catalog, parse_library_id
from app.ingest.models import parsed_doc_chunk_from_parser
from app.ingest.parser import parse_document
from app.retrieval.qdrant import QdrantAdapter
from app.settings import get_settings
from app.store import save_chunks

cli = typer.Typer()


@cli.callback()
def callback() -> None:
    return


@cli.command()
def ingest(
    library: Annotated[str, typer.Option()],
    source_dir: Annotated[Path, typer.Option()],
    version: Annotated[str, typer.Option()] = "main",
) -> None:
    catalog = find_catalog(library)
    include = catalog.library.source.include if catalog is not None else ("**/*.md", "**/*.mdx")
    exclude = catalog.library.source.exclude if catalog is not None else ()
    parsed_chunks = [
        parsed_doc_chunk_from_parser(chunk)
        for path in selected_paths(source_dir, include, exclude)
        for chunk in parse_document(path)
    ]
    chunks = save_chunks(parsed_chunks, library_id=library, version=version)
    settings = get_settings()
    if settings.retrieval_mode == "qdrant":
        adapter = QdrantAdapter(
            QdrantClient(url=settings.qdrant_url, check_compatibility=False)
        )
        adapter.replace_chunks(library, version, chunks)
    typer.echo(f"ingested {len(chunks)} chunks")


def find_catalog(library_id: str) -> Catalog | None:
    parsed = parse_library_id(library_id)
    catalog_dir = Path("libraries")
    if not catalog_dir.exists():
        return None
    for path in sorted(catalog_dir.glob("*.yaml")):
        catalog = load_catalog(path)
        if catalog.library.base_id == parsed.base_id:
            return catalog
    return None


def selected_paths(
    source_dir: Path,
    include: tuple[str, ...],
    exclude: tuple[str, ...],
) -> list[Path]:
    source_root = source_dir.resolve(strict=True)
    included: set[Path] = set()
    for pattern in include:
        for path in source_root.glob(pattern):
            if not path.is_file():
                continue
            resolved = path.resolve(strict=True)
            if not resolved.is_relative_to(source_root):
                message = f"matched file escapes source directory: {path}"
                raise typer.BadParameter(message)
            included.add(path)
    return sorted(path for path in included if not is_excluded(source_root, path, exclude))


def is_excluded(source_dir: Path, path: Path, exclude: tuple[str, ...]) -> bool:
    relative = path.relative_to(source_dir).as_posix()
    return any(
        fnmatch(relative, pattern) or fnmatch(relative, pattern.removeprefix("**/"))
        for pattern in exclude
    )


def main() -> None:
    cli()
