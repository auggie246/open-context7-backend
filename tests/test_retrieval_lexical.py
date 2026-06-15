from app.ingest.models import DocChunk, DocChunkKind
from app.retrieval.lexical import LexicalRetriever


def make_chunk(
    chunk_id: str,
    content: str,
    source_path: str,
    index: int,
    *,
    token_count: int = 4,
    kind: DocChunkKind = DocChunkKind.PROSE,
) -> DocChunk:
    return DocChunk(
        id=chunk_id,
        library_id="/internal/platform",
        version="main",
        source_path=source_path,
        heading="Guide",
        chunk_index=index,
        language=None,
        kind=kind,
        token_count=token_count,
        content=content,
    )


def test_lexical_retriever_when_query_matches_scores_and_orders_stably() -> None:
    retriever = LexicalRetriever(
        [
            make_chunk("b", "valuesFrom helm config", "b.mdx", 0),
            make_chunk("a", "valuesFrom helm config", "a.mdx", 0),
            make_chunk("c", "unrelated content", "c.mdx", 0),
        ]
    )

    results = retriever.search("/internal/platform", "main", "helm valuesFrom", max_tokens=10)

    assert [chunk.id for chunk in results] == ["a", "b"]


def test_lexical_retriever_when_token_budget_small_stops_in_order() -> None:
    retriever = LexicalRetriever(
        [
            make_chunk("a", "valuesFrom helm", "a.mdx", 0, token_count=6),
            make_chunk("b", "valuesFrom helm", "b.mdx", 0, token_count=6),
        ]
    )

    results = retriever.search("/internal/platform", "main", "valuesFrom", max_tokens=6)

    assert [chunk.id for chunk in results] == ["a"]
