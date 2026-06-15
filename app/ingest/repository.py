from app.ingest.models import DocChunk, ParsedDocChunk, materialize_chunk


class InMemoryChunkRepository:
    def __init__(self) -> None:
        self._chunks: dict[tuple[str, str, str], DocChunk] = {}

    def replace_library_chunks(
        self,
        library_id: str,
        version: str,
        chunks: list[ParsedDocChunk],
    ) -> list[DocChunk]:
        materialized = [materialize_chunk(library_id, version, chunk) for chunk in chunks]
        current_ids = {chunk.id for chunk in materialized}
        stale_keys = [
            key
            for key, chunk in self._chunks.items()
            if chunk.library_id == library_id
            and chunk.version == version
            and chunk.id not in current_ids
        ]
        for key in stale_keys:
            del self._chunks[key]
        for chunk in materialized:
            self._chunks[(chunk.library_id, chunk.version, chunk.id)] = chunk
        return materialized

    def list_chunks(self, library_id: str, version: str) -> list[DocChunk]:
        return sorted(
            [
                chunk
                for chunk in self._chunks.values()
                if chunk.library_id == library_id and chunk.version == version
            ],
            key=lambda chunk: (chunk.source_path, chunk.heading, chunk.chunk_index),
        )
