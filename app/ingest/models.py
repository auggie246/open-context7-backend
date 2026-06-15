import hashlib
from dataclasses import dataclass
from enum import StrEnum

from app.ingest.parser import ChunkKind, ParsedChunk


class DocChunkKind(StrEnum):
    CODE = "code"
    PROSE = "prose"


@dataclass(frozen=True, slots=True)
class ParsedDocChunk:
    source_path: str
    heading: str
    chunk_index: int
    language: str | None
    start_line: int
    end_line: int
    kind: DocChunkKind
    token_count: int
    content: str


@dataclass(frozen=True, slots=True)
class DocChunk:
    id: str
    library_id: str
    version: str
    source_path: str
    heading: str
    chunk_index: int
    language: str | None
    kind: DocChunkKind
    token_count: int
    content: str
    start_line: int = 1
    end_line: int = 1


def parsed_doc_chunk_from_parser(chunk: ParsedChunk) -> ParsedDocChunk:
    match chunk.kind:
        case ChunkKind.CODE:
            kind = DocChunkKind.CODE
        case ChunkKind.PROSE:
            kind = DocChunkKind.PROSE
    return ParsedDocChunk(
        source_path=chunk.source_path,
        heading=chunk.heading,
        chunk_index=chunk.chunk_index,
        language=chunk.language,
        start_line=chunk.start_line,
        end_line=chunk.end_line,
        kind=kind,
        token_count=chunk.token_count,
        content=chunk.content,
    )


def stable_chunk_id(library_id: str, version: str, chunk: ParsedDocChunk) -> str:
    digest = hashlib.sha256()
    for value in (
        library_id,
        version,
        chunk.source_path,
        str(chunk.chunk_index),
        "\n".join(chunk.content.split()),
    ):
        digest.update(value.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def materialize_chunk(library_id: str, version: str, chunk: ParsedDocChunk) -> DocChunk:
    return DocChunk(
        id=stable_chunk_id(library_id, version, chunk),
        library_id=library_id,
        version=version,
        source_path=chunk.source_path,
        heading=chunk.heading,
        chunk_index=chunk.chunk_index,
        language=chunk.language,
        kind=chunk.kind,
        token_count=chunk.token_count,
        content=chunk.content,
        start_line=chunk.start_line,
        end_line=chunk.end_line,
    )
