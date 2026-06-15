from app.embeddings import DeterministicEmbeddingClient
from app.rerank import maybe_rerank


def test_deterministic_embedding_when_same_text_returns_same_vector() -> None:
    client = DeterministicEmbeddingClient(size=8)

    assert client.embed("valuesFrom") == client.embed("valuesFrom")


def test_maybe_rerank_when_fast_or_disabled_preserves_order() -> None:
    chunks = ["a", "b", "c"]

    assert maybe_rerank(chunks, enabled=False, fast=False) == chunks
    assert maybe_rerank(chunks, enabled=True, fast=True) == chunks
