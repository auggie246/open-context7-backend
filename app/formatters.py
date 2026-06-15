import json
import sys
from pathlib import Path

from pydantic import TypeAdapter

from app.ingest.models import DocChunk, DocChunkKind
from app.models import CodeExample, CodeSnippet, ContextResponse, InfoSnippet


def format_text_context(chunks: list[DocChunk]) -> str:
    if not chunks:
        return "No relevant snippets found for this query."
    snippets = [_format_text_chunk(chunk) for chunk in chunks]
    return (
        "\n----------------------------------------\n".join(snippets)
        + "\n----------------------------------------"
    )


def _format_text_chunk(chunk: DocChunk) -> str:
    label = "CODE" if chunk.kind is DocChunkKind.CODE else "CONTENT"
    language = chunk.language or "text"
    return "\n".join(
        [
            f"TITLE: {chunk.heading or chunk.source_path}",
            f"DESCRIPTION: {chunk.heading or chunk.source_path}",
            f"SOURCE: {chunk.source_path}#L{chunk.start_line}",
            f"LANGUAGE: {language}",
            f"{label}:",
            chunk.content,
        ]
    )


def format_json_context(chunks: list[DocChunk]) -> ContextResponse:
    code_snippets: list[CodeSnippet] = []
    info_snippets: list[InfoSnippet] = []
    for chunk in chunks:
        match chunk.kind:
            case DocChunkKind.CODE:
                language = chunk.language or "text"
                code_snippets.append(
                    CodeSnippet(
                        codeTitle=chunk.heading or chunk.source_path,
                        codeDescription=chunk.heading or chunk.source_path,
                        codeLanguage=language,
                        codeTokens=chunk.token_count,
                        codeId=f"{chunk.source_path}#L{chunk.start_line}",
                        pageTitle=chunk.heading or chunk.source_path,
                        codeList=[CodeExample(language=language, code=chunk.content)],
                    )
                )
            case DocChunkKind.PROSE:
                info_snippets.append(
                    InfoSnippet(
                        pageId=f"{chunk.source_path}#L{chunk.start_line}",
                        breadcrumb=chunk.heading or None,
                        content=chunk.content,
                        contentTokens=chunk.token_count,
                    )
                )
    return ContextResponse(codeSnippets=code_snippets, infoSnippets=info_snippets)


def _load_chunks(path: Path) -> list[DocChunk]:
    adapter = TypeAdapter(list[DocChunk])
    return adapter.validate_json(path.read_text(encoding="utf-8"))


def main() -> None:
    mode = sys.argv[1]
    chunks = _load_chunks(Path(sys.argv[2]))
    match mode:
        case "--txt":
            _ = sys.stdout.write(format_text_context(chunks))
        case "--json":
            _ = sys.stdout.write(
                json.dumps(format_json_context(chunks).model_dump(), sort_keys=True)
            )
        case _:
            message = "usage: python -m app.formatters --txt|--json <chunks.json>"
            raise SystemExit(message)


if __name__ == "__main__":
    main()
