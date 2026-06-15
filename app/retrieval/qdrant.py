import sys
import uuid
import warnings
from dataclasses import dataclass
from typing import Protocol, TypedDict, cast

from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.embeddings import DeterministicEmbeddingClient
from app.ingest.models import DocChunk, DocChunkKind

DEFAULT_COLLECTION = "docs"
PAYLOAD_INDEXES = ("library_id", "version", "kind", "source_path")
POINT_NAMESPACE = uuid.UUID("0a086dad-1a29-430c-8e72-c204e9570423")


class EmbeddingClient(Protocol):
    def embed(self, text: str) -> list[float]: ...


@dataclass(frozen=True, slots=True)
class QdrantQuery:
    library_id: str
    version: str
    query: str
    kind: DocChunkKind | None = None
    source_path: str | None = None
    limit: int = 8


class ChunkPayload(TypedDict):
    id: str
    library_id: str
    version: str
    kind: str
    source_path: str
    heading: str
    chunk_index: int
    language: str | None
    token_count: int
    content: str
    start_line: int
    end_line: int


class QdrantAdapter:
    def __init__(
        self,
        client: QdrantClient,
        *,
        embedding_client: EmbeddingClient | None = None,
        collection_name: str = DEFAULT_COLLECTION,
        vector_size: int = 32,
    ) -> None:
        self._client: QdrantClient = client
        self._embedding_client: EmbeddingClient = embedding_client or DeterministicEmbeddingClient(
            size=vector_size
        )
        self._collection_name: str = collection_name
        self._vector_size: int = vector_size

    def ensure_collection(self) -> None:
        if not self._client.collection_exists(self._collection_name):
            _ = self._client.create_collection(
                collection_name=self._collection_name,
                vectors_config=models.VectorParams(
                    size=self._vector_size,
                    distance=models.Distance.COSINE,
                ),
            )
        for field_name in PAYLOAD_INDEXES:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="Payload indexes have no effect.*")
                _ = self._client.create_payload_index(
                    collection_name=self._collection_name,
                    field_name=field_name,
                    field_schema=models.PayloadSchemaType.KEYWORD,
                    wait=True,
                )

    def replace_chunks(self, library_id: str, version: str, chunks: list[DocChunk]) -> None:
        self.ensure_collection()
        self.delete_library_version(library_id, version)
        self.upsert_chunks(chunks)

    def upsert_chunks(self, chunks: list[DocChunk]) -> None:
        if not chunks:
            return
        points = [
            models.PointStruct(
                id=point_id(chunk.id),
                vector=self._embedding_client.embed(chunk.content),
                payload=dict(chunk_payload(chunk)),
            )
            for chunk in chunks
        ]
        _ = self._client.upsert(
            collection_name=self._collection_name,
            points=points,
            wait=True,
        )

    def delete_orphans(self, ids: list[str]) -> None:
        if not ids:
            return
        _ = self._client.delete(
            collection_name=self._collection_name,
            points_selector=models.PointIdsList(points=[point_id(value) for value in ids]),
            wait=True,
        )

    def delete_library_version(self, library_id: str, version: str) -> None:
        _ = self._client.delete(
            collection_name=self._collection_name,
            points_selector=models.FilterSelector(
                filter=payload_filter(library_id=library_id, version=version),
            ),
            wait=True,
        )

    def query(self, request: QdrantQuery) -> list[DocChunk]:
        response = self._client.query_points(
            collection_name=self._collection_name,
            query=self._embedding_client.embed(request.query),
            query_filter=payload_filter(
                library_id=request.library_id,
                version=request.version,
                kind=request.kind,
                source_path=request.source_path,
            ),
            limit=request.limit,
            with_payload=True,
        )
        chunks: list[DocChunk] = []
        for point in response.points:
            payload = payload_from_raw(point.payload)
            if payload is not None:
                chunks.append(payload_to_chunk(payload))
        return chunks


def point_id(chunk_id: str) -> str:
    return str(uuid.uuid5(POINT_NAMESPACE, chunk_id))


def chunk_payload(chunk: DocChunk) -> ChunkPayload:
    return {
        "id": chunk.id,
        "library_id": chunk.library_id,
        "version": chunk.version,
        "kind": chunk.kind.value,
        "source_path": chunk.source_path,
        "heading": chunk.heading,
        "chunk_index": chunk.chunk_index,
        "language": chunk.language,
        "token_count": chunk.token_count,
        "content": chunk.content,
        "start_line": chunk.start_line,
        "end_line": chunk.end_line,
    }


def payload_filter(
    *,
    library_id: str,
    version: str,
    kind: DocChunkKind | None = None,
    source_path: str | None = None,
) -> models.Filter:
    conditions: list[models.Condition] = [
        field_condition("library_id", library_id),
        field_condition("version", version),
    ]
    if kind is not None:
        conditions.append(field_condition("kind", kind.value))
    if source_path is not None:
        conditions.append(field_condition("source_path", source_path))
    return models.Filter(must=conditions)


def field_condition(field_name: str, value: str) -> models.FieldCondition:
    return models.FieldCondition(key=field_name, match=models.MatchValue(value=value))


def payload_from_raw(raw: object) -> ChunkPayload | None:
    if not isinstance(raw, dict):
        return None
    raw_payload = cast("dict[object, object]", raw)
    try:
        return {
            "id": require_string(raw_payload, "id"),
            "library_id": require_string(raw_payload, "library_id"),
            "version": require_string(raw_payload, "version"),
            "kind": require_string(raw_payload, "kind"),
            "source_path": require_string(raw_payload, "source_path"),
            "heading": require_string(raw_payload, "heading"),
            "chunk_index": require_int(raw_payload, "chunk_index"),
            "language": optional_string(raw_payload.get("language")),
            "token_count": require_int(raw_payload, "token_count"),
            "content": require_string(raw_payload, "content"),
            "start_line": require_int(raw_payload, "start_line"),
            "end_line": require_int(raw_payload, "end_line"),
        }
    except (KeyError, TypeError, ValueError):
        return None


def payload_to_chunk(payload: ChunkPayload) -> DocChunk:
    return DocChunk(
        id=payload["id"],
        library_id=payload["library_id"],
        version=payload["version"],
        source_path=payload["source_path"],
        heading=payload["heading"],
        chunk_index=payload["chunk_index"],
        language=payload["language"],
        kind=DocChunkKind(payload["kind"]),
        token_count=payload["token_count"],
        content=payload["content"],
        start_line=payload["start_line"],
        end_line=payload["end_line"],
    )


def optional_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def require_string(payload: dict[object, object], key: str) -> str:
    value = payload[key]
    if not isinstance(value, str):
        raise TypeError(key)
    return value


def require_int(payload: dict[object, object], key: str) -> int:
    value = payload[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(key)
    return value


def main() -> None:
    if "--smoke" not in sys.argv:
        return
    client = QdrantClient(
        url="http://127.0.0.1:6333",
        timeout=10,
        check_compatibility=False,
    )
    adapter = QdrantAdapter(client)
    chunk = DocChunk(
        id="smoke-1",
        library_id="/internal/platform",
        version="main",
        source_path="smoke.mdx",
        heading="Smoke",
        chunk_index=0,
        language="bash",
        kind=DocChunkKind.CODE,
        token_count=2,
        content="helm valuesFrom",
    )
    adapter.replace_chunks(chunk.library_id, chunk.version, [chunk])
    found = adapter.query(
        QdrantQuery(
            library_id=chunk.library_id,
            version=chunk.version,
            query="valuesFrom",
            kind=DocChunkKind.CODE,
            source_path=chunk.source_path,
            limit=1,
        )
    )
    schema = client.get_collection(DEFAULT_COLLECTION).payload_schema
    _ = sys.stdout.write(
        "\n".join(
            [
                "collection:docs",
                f"payload_indexes:{','.join(sorted(schema))}",
                f"query_results:{len(found)}",
                f"first_id:{found[0].id if found else ''}",
            ]
        )
    )


if __name__ == "__main__":
    main()
