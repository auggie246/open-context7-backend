import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from pydantic import TypeAdapter

from app.ingest.models import DocChunk, DocChunkKind

TOKEN_PATTERN: Final[re.Pattern[str]] = re.compile(r"[A-Za-z0-9_]+")


@dataclass(frozen=True, slots=True)
class ScoredChunk:
    score: int
    chunk: DocChunk


class LexicalRetriever:
    def __init__(self, chunks: list[DocChunk]) -> None:
        self._chunks: list[DocChunk] = chunks

    def search(
        self,
        library_id: str,
        version: str,
        query: str,
        *,
        max_tokens: int,
        kind: DocChunkKind | None = None,
    ) -> list[DocChunk]:
        query_tokens = set(tokenize(query))
        scored = [
            ScoredChunk(score=len(query_tokens & set(tokenize(chunk.content))), chunk=chunk)
            for chunk in self._chunks
            if chunk.library_id == library_id
            and chunk.version == version
            and kind in (None, chunk.kind)
        ]
        ordered = sorted(
            [item for item in scored if item.score > 0],
            key=lambda item: (
                -item.score,
                item.chunk.source_path,
                item.chunk.heading,
                item.chunk.chunk_index,
            ),
        )
        results: list[DocChunk] = []
        used_tokens = 0
        for item in ordered:
            if results and used_tokens + item.chunk.token_count > max_tokens:
                break
            results.append(item.chunk)
            used_tokens += item.chunk.token_count
        return results


def tokenize(value: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_PATTERN.finditer(value)]


def _load_chunks(path: Path) -> list[DocChunk]:
    adapter = TypeAdapter(list[DocChunk])
    return adapter.validate_json(path.read_text(encoding="utf-8"))


def main() -> None:
    fixture = Path(sys.argv[sys.argv.index("--fixture") + 1])
    query = sys.argv[sys.argv.index("--query") + 1]
    chunks = LexicalRetriever(_load_chunks(fixture)).search(
        "/internal/platform",
        "main",
        query,
        max_tokens=5000,
    )
    _ = sys.stdout.write(json.dumps([chunk.id for chunk in chunks]))


if __name__ == "__main__":
    main()
