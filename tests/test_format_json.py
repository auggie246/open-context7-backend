from app.formatters import format_json_context
from app.ingest.models import DocChunk, DocChunkKind


def test_format_json_context_when_chunks_have_code_and_prose_maps_required_fields() -> None:
    response = format_json_context(
        [
            DocChunk(
                id="code-1",
                library_id="/internal/platform",
                version="main",
                source_path="guide.mdx",
                heading="Install",
                chunk_index=0,
                language="bash",
                kind=DocChunkKind.CODE,
                token_count=4,
                content="helm upgrade platform",
            ),
            DocChunk(
                id="prose-1",
                library_id="/internal/platform",
                version="main",
                source_path="guide.mdx",
                heading="Configure",
                chunk_index=1,
                language=None,
                kind=DocChunkKind.PROSE,
                token_count=5,
                content="Use valuesFrom for config.",
            ),
        ]
    )

    assert response.codeSnippets[0].codeTitle == "Install"
    assert response.codeSnippets[0].codeList[0].code == "helm upgrade platform"
    assert response.infoSnippets[0].content == "Use valuesFrom for config."
