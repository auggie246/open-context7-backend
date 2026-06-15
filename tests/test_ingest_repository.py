from app.ingest.models import DocChunkKind, ParsedDocChunk, stable_chunk_id
from app.ingest.repository import InMemoryChunkRepository


def make_parsed(content: str, index: int) -> ParsedDocChunk:
    return ParsedDocChunk(
        source_path="guide.mdx",
        heading="Guide",
        chunk_index=index,
        language=None,
        start_line=1,
        end_line=1,
        kind=DocChunkKind.PROSE,
        token_count=3,
        content=content,
    )


def test_stable_chunk_id_when_content_same_returns_same_id() -> None:
    first = stable_chunk_id("/internal/platform", "main", make_parsed("same", 0))
    second = stable_chunk_id("/internal/platform", "main", make_parsed("same", 0))

    assert first == second


def test_repository_when_reingested_deletes_orphans() -> None:
    repository = InMemoryChunkRepository()
    first = repository.replace_library_chunks(
        "/internal/platform",
        "main",
        [make_parsed("first", 0), make_parsed("second", 1)],
    )

    second = repository.replace_library_chunks(
        "/internal/platform",
        "main",
        [make_parsed("first", 0)],
    )

    assert len(first) == 2
    assert len(second) == 1
    assert [chunk.content for chunk in repository.list_chunks("/internal/platform", "main")] == [
        "first"
    ]
