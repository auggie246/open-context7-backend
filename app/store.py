from pathlib import Path

from pydantic import TypeAdapter

from app.ingest.models import DocChunk, ParsedDocChunk, materialize_chunk

DEFAULT_STORE_PATH = Path(".omo/local-store/chunks.json")


def save_chunks(
    chunks: list[DocChunk] | list[ParsedDocChunk],
    *,
    library_id: str = "/internal/platform",
    version: str = "main",
    path: Path = DEFAULT_STORE_PATH,
) -> list[DocChunk]:
    materialized = [
        chunk if isinstance(chunk, DocChunk) else materialize_chunk(library_id, version, chunk)
        for chunk in chunks
    ]
    existing = [
        chunk
        for chunk in load_chunks(path)
        if chunk.library_id != library_id or chunk.version != version
    ]
    merged = sorted(
        [*existing, *materialized],
        key=lambda chunk: (chunk.library_id, chunk.version, chunk.source_path, chunk.chunk_index),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(
        TypeAdapter(list[DocChunk]).dump_json(merged).decode("utf-8"),
        encoding="utf-8",
    )
    return materialized


def load_chunks(path: Path = DEFAULT_STORE_PATH) -> list[DocChunk]:
    if not path.exists():
        return []
    return TypeAdapter(list[DocChunk]).validate_json(path.read_text(encoding="utf-8"))
