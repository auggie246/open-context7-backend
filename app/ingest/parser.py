from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final, Literal, TypedDict

import orjson

TOKEN_PATTERN: Final = re.compile(r"[A-Za-z0-9_]+")
HEADING_PATTERN: Final = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
FENCE_PATTERN: Final = re.compile(r"^(```|~~~)\s*([A-Za-z0-9_+.-]*)?.*$")
MDX_IMPORT_PATTERN: Final = re.compile(r"^\s*(import|export)\s+")
JSX_BLOCK_PATTERN: Final = re.compile(r"^\s*<[A-Z][A-Za-z0-9]*(\s|>|/>)")


class ChunkKind(StrEnum):
    CODE = "code"
    PROSE = "prose"


class ParsedChunkRecord(TypedDict):
    source_path: str
    heading: str
    chunk_index: int
    language: str | None
    start_line: int
    end_line: int
    kind: Literal["code", "prose"]
    token_count: int
    content: str


@dataclass(frozen=True, slots=True)
class ParsedChunk:
    source_path: str
    heading: str
    chunk_index: int
    language: str | None
    start_line: int
    end_line: int
    kind: ChunkKind
    token_count: int
    content: str

    def to_record(self) -> ParsedChunkRecord:
        return {
            "source_path": self.source_path,
            "heading": self.heading,
            "chunk_index": self.chunk_index,
            "language": self.language,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "kind": self.kind.value,
            "token_count": self.token_count,
            "content": self.content,
        }


@dataclass(frozen=True, slots=True)
class ProseBuffer:
    lines: tuple[str, ...]
    start_line: int
    end_line: int


@dataclass(frozen=True, slots=True)
class ChunkBuildRequest:
    source_path: str
    heading: str
    chunk_index: int
    language: str | None
    start_line: int
    end_line: int
    kind: ChunkKind
    content: str


def parse_document(path: Path) -> list[ParsedChunk]:
    with path.open("r", encoding="utf-8") as handle:
        return parse_markdown(path.as_posix(), handle.read())


def parse_markdown(source_path: str, content: str) -> list[ParsedChunk]:
    lines = content.splitlines()
    body_start = frontmatter_end_line(lines)
    chunks: list[ParsedChunk] = []
    prose_lines: list[str] = []
    prose_start = 0
    heading = ""
    line_index = body_start

    while line_index < len(lines):
        line = lines[line_index]
        line_number = line_index + 1

        if is_mdx_import(line):
            line_index += 1
            continue

        heading_match = HEADING_PATTERN.match(line)
        if heading_match is not None:
            append_prose_chunk(
                chunks,
                ProseBuffer(tuple(prose_lines), prose_start, line_number - 1),
                source_path,
                heading,
            )
            prose_lines = []
            prose_start = 0
            heading = heading_match.group(2).strip()
            line_index += 1
            continue

        fence_match = FENCE_PATTERN.match(line)
        if fence_match is not None:
            append_prose_chunk(
                chunks,
                ProseBuffer(tuple(prose_lines), prose_start, line_number - 1),
                source_path,
                heading,
            )
            prose_lines = []
            prose_start = 0
            fence = collect_fence(lines, line_index, fence_match.group(1))
            chunks.append(
                build_chunk(
                    ChunkBuildRequest(
                        source_path=source_path,
                        heading=heading,
                        chunk_index=len(chunks),
                        language=fence.language,
                        start_line=fence.start_line,
                        end_line=fence.end_line,
                        kind=ChunkKind.CODE,
                        content=fence.content,
                    )
                )
            )
            line_index = fence.next_index
            continue

        if is_jsx_block_start(line):
            append_prose_chunk(
                chunks,
                ProseBuffer(tuple(prose_lines), prose_start, line_number - 1),
                source_path,
                heading,
            )
            prose_lines = []
            prose_start = 0
            line_index = skip_jsx_block(lines, line_index)
            continue

        if line.strip():
            if not prose_lines:
                prose_start = line_number
            prose_lines.append(line.strip())
        else:
            append_prose_chunk(
                chunks,
                ProseBuffer(tuple(prose_lines), prose_start, line_number - 1),
                source_path,
                heading,
            )
            prose_lines = []
            prose_start = 0
        line_index += 1

    append_prose_chunk(
        chunks,
        ProseBuffer(tuple(prose_lines), prose_start, len(lines)),
        source_path,
        heading,
    )
    return chunks


@dataclass(frozen=True, slots=True)
class FenceBlock:
    content: str
    language: str | None
    start_line: int
    end_line: int
    next_index: int


def frontmatter_end_line(lines: list[str]) -> int:
    if not lines or lines[0].strip() != "---":
        return 0
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return index + 1
    return 0


def is_mdx_import(line: str) -> bool:
    return MDX_IMPORT_PATTERN.match(line) is not None


def is_jsx_block_start(line: str) -> bool:
    return JSX_BLOCK_PATTERN.match(line) is not None


def skip_jsx_block(lines: list[str], start_index: int) -> int:
    first_line = lines[start_index].strip()
    if first_line.endswith("/>"):
        return start_index + 1
    tag_name = first_line.removeprefix("<").split(maxsplit=1)[0].rstrip(">")
    closing = f"</{tag_name}>"
    for index, line in enumerate(lines[start_index + 1 :], start=start_index + 1):
        if line.strip().startswith(closing):
            return index + 1
    return start_index + 1


def collect_fence(lines: list[str], start_index: int, fence_marker: str) -> FenceBlock:
    opening = lines[start_index]
    language = parse_fence_language(opening)
    end_index = start_index
    for index, line in enumerate(lines[start_index + 1 :], start=start_index + 1):
        end_index = index
        if line.startswith(fence_marker):
            break
    else:
        end_index = len(lines) - 1
    return FenceBlock(
        content="\n".join(lines[start_index : end_index + 1]),
        language=language,
        start_line=start_index + 1,
        end_line=end_index + 1,
        next_index=end_index + 1,
    )


def parse_fence_language(opening: str) -> str | None:
    match = FENCE_PATTERN.match(opening)
    if match is None:
        return None
    language = match.group(2)
    if language is None or not language:
        return None
    return language


def append_prose_chunk(
    chunks: list[ParsedChunk],
    buffer: ProseBuffer,
    source_path: str,
    heading: str,
) -> None:
    if not buffer.lines:
        return
    content = "\n".join(buffer.lines)
    chunks.append(
        build_chunk(
            ChunkBuildRequest(
                source_path=source_path,
                heading=heading,
                chunk_index=len(chunks),
                language=None,
                start_line=buffer.start_line,
                end_line=buffer.end_line,
                kind=ChunkKind.PROSE,
                content=content,
            )
        )
    )


def build_chunk(request: ChunkBuildRequest) -> ParsedChunk:
    return ParsedChunk(
        source_path=request.source_path,
        heading=request.heading,
        chunk_index=request.chunk_index,
        language=request.language,
        start_line=request.start_line,
        end_line=request.end_line,
        kind=request.kind,
        token_count=count_tokens(request.content),
        content=request.content,
    )


def count_tokens(content: str) -> int:
    return len(TOKEN_PATTERN.findall(content))


def main() -> None:
    for chunk in parse_document(Path(sys.argv[1])):
        _ = sys.stdout.buffer.write(orjson.dumps(chunk.to_record()))
        _ = sys.stdout.buffer.write(b"\n")


if __name__ == "__main__":
    main()
