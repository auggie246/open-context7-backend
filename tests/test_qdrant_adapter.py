from app.ingest.models import DocChunk, DocChunkKind
from app.retrieval.qdrant import QdrantAdapter, QdrantQuery
from qdrant_client import QdrantClient


def test_qdrant_adapter_uses_real_collection_indexes_and_filtered_query() -> None:
    client = QdrantClient(location=":memory:")
    adapter = QdrantAdapter(client)
    target = chunk("id-1", "/internal/platform", "main", "guide.mdx", DocChunkKind.CODE)
    other_library = chunk("id-2", "/other/library", "main", "guide.mdx", DocChunkKind.CODE)
    other_kind = chunk("id-3", "/internal/platform", "main", "guide.mdx", DocChunkKind.PROSE)
    other_source = chunk("id-4", "/internal/platform", "main", "other.mdx", DocChunkKind.CODE)

    adapter.replace_chunks(
        "/internal/platform",
        "main",
        [target, other_library, other_kind, other_source],
    )

    found = adapter.query(
        QdrantQuery(
            library_id="/internal/platform",
            version="main",
            query="valuesFrom",
            kind=DocChunkKind.CODE,
            source_path="guide.mdx",
            limit=3,
        )
    )

    assert [item.id for item in found] == ["id-1"]

    adapter.delete_orphans(["id-1"])
    after_delete = adapter.query(
        QdrantQuery(
            library_id="/internal/platform",
            version="main",
            query="valuesFrom",
            kind=DocChunkKind.CODE,
            source_path="guide.mdx",
            limit=3,
        )
    )
    assert after_delete == []


def chunk(
    chunk_id: str,
    library_id: str,
    version: str,
    source_path: str,
    kind: DocChunkKind,
) -> DocChunk:
    return DocChunk(
        id=chunk_id,
        library_id=library_id,
        version=version,
        source_path=source_path,
        heading="Guide",
        chunk_index=0,
        language="bash" if kind is DocChunkKind.CODE else None,
        kind=kind,
        token_count=2,
        content="helm valuesFrom",
    )
