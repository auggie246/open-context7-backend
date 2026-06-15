from pathlib import Path

from app.ingest.parser import ChunkKind, parse_document

FIXTURE_PATH = Path("tests/fixtures/docs/guide.mdx")


def test_parse_document_when_frontmatter_and_mdx_present_returns_stable_chunks() -> None:
    # Given
    source_path = FIXTURE_PATH

    # When
    chunks = parse_document(source_path)

    # Then
    assert [chunk.kind for chunk in chunks] == [
        ChunkKind.PROSE,
        ChunkKind.PROSE,
        ChunkKind.CODE,
        ChunkKind.PROSE,
        ChunkKind.CODE,
        ChunkKind.PROSE,
    ]
    assert [chunk.chunk_index for chunk in chunks] == list(range(6))
    assert {chunk.source_path for chunk in chunks} == {source_path.as_posix()}
    assert chunks[0].heading == "Platform Guide"
    assert chunks[0].content == "Intro text explains valuesFrom and platform setup."
    assert chunks[0].start_line == 9
    assert chunks[0].end_line == 9
    assert chunks[0].token_count == 7
    assert "title: Platform Guide" not in chunks[0].content
    assert "import Tabs" not in chunks[0].content
    assert "<Callout" not in chunks[0].content


def test_parse_document_when_fenced_blocks_present_preserves_fence_content() -> None:
    # Given
    source_path = FIXTURE_PATH

    # When
    chunks = parse_document(source_path)

    # Then
    bash_chunk = chunks[2]
    ts_chunk = chunks[4]
    assert bash_chunk.kind is ChunkKind.CODE
    assert bash_chunk.heading == "Install"
    assert bash_chunk.language == "bash"
    assert bash_chunk.start_line == 19
    assert bash_chunk.end_line == 22
    assert bash_chunk.content == (
        "```bash\nhelm upgrade platform ./chart \\\n  --set valuesFrom=config.yaml\n```"
    )
    assert bash_chunk.token_count == 9
    assert ts_chunk.kind is ChunkKind.CODE
    assert ts_chunk.heading == "Configure"
    assert ts_chunk.language == "ts"
    assert ts_chunk.content == (
        '```ts\nexport const valuesFrom = ["config.yaml", "secret.yaml"];\n```'
    )


def test_parse_document_when_reparsed_returns_deterministic_chunks() -> None:
    # Given
    source_path = FIXTURE_PATH

    # When
    first = parse_document(source_path)
    second = parse_document(source_path)

    # Then
    assert first == second
