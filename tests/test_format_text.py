from app.formatters import format_text_context
from app.ingest.models import DocChunk, DocChunkKind


def test_format_text_context_when_chunks_exist_uses_context7_snippet_shape() -> None:
    chunks = [
        DocChunk(
            id="chunk-1",
            library_id="/internal/platform",
            version="main",
            source_path="guide.mdx",
            heading="Install",
            chunk_index=0,
            language="bash",
            kind=DocChunkKind.CODE,
            token_count=4,
            content="helm upgrade platform",
        )
    ]

    text = format_text_context(chunks)

    assert "TITLE: Install" in text
    assert "SOURCE: guide.mdx#L1" in text
    assert "LANGUAGE: bash" in text
    assert "CODE:\nhelm upgrade platform" in text
    assert "----------------------------------------" in text


def test_format_text_context_when_no_chunks_returns_non_empty_message() -> None:
    assert format_text_context([]).startswith("No relevant snippets found")
