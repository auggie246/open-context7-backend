from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse, PlainTextResponse
from qdrant_client import QdrantClient

from app.auth import require_bearer_auth
from app.catalog import Catalog, ParsedLibraryId, load_catalog, parse_library_id
from app.formatters import format_json_context, format_text_context
from app.ingest.models import DocChunk
from app.models import ContextResponse, Library, LibraryState, SearchResponse
from app.retrieval.lexical import LexicalRetriever
from app.retrieval.qdrant import QdrantAdapter, QdrantQuery
from app.settings import get_settings
from app.store import load_chunks

router = APIRouter(prefix="/api/v2", dependencies=[Depends(require_bearer_auth)])


@router.get("/libs/search")
def search_libraries(
    query: Annotated[str, Query(min_length=1, max_length=500)],
    libraryName: Annotated[str, Query(min_length=1, max_length=500)],  # noqa: N803
    fast: Literal["true", "false"] = "false",
) -> SearchResponse:
    _ = fast
    catalogs = load_catalogs(Path("libraries"))
    results = [
        catalog_to_library(catalog) for catalog in rank_catalogs(catalogs, query, libraryName)
    ]
    return SearchResponse(results=results, searchFilterApplied=False)


@router.get("/context", response_model=None)
def get_context(
    query: Annotated[str, Query(min_length=1, max_length=500)],
    libraryId: Annotated[str, Query(min_length=1, max_length=500)],  # noqa: N803
    type: Literal["json", "txt"] = "txt",  # noqa: A002
    fast: Literal["true", "false"] = "false",
) -> ContextResponse | PlainTextResponse | JSONResponse:
    catalog = find_catalog(libraryId)
    if catalog is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "not_found", "message": "Library not found"},
        )
    chunks = retrieve_chunks(
        catalog.library.base_id,
        catalog.library.version or "main",
        query,
        max_tokens=5000,
    )
    _ = fast
    match type:
        case "json":
            return format_json_context(chunks)
        case "txt":
            return PlainTextResponse(format_text_context(chunks))


def load_catalogs(directory: Path) -> list[Catalog]:
    if not directory.exists():
        return []
    return [load_catalog(path) for path in sorted(directory.glob("*.yaml"))]


def retrieve_chunks(
    library_id: str,
    version: str,
    query: str,
    *,
    max_tokens: int,
) -> list[DocChunk]:
    settings = get_settings()
    if settings.retrieval_mode == "qdrant":
        return QdrantAdapter(
            QdrantClient(url=settings.qdrant_url, check_compatibility=False)
        ).query(
            QdrantQuery(library_id=library_id, version=version, query=query, limit=8)
        )
    return LexicalRetriever(load_chunks()).search(
        library_id,
        version,
        query,
        max_tokens=max_tokens,
    )


def find_catalog(library_id: str) -> Catalog | None:
    parsed = parse_library_id(library_id)
    for catalog in load_catalogs(Path("libraries")):
        if catalog_matches_id(catalog, parsed):
            version = parsed.version or catalog.library.version or "main"
            catalog_version = catalog.library.version or "main"
            if version in catalog.library.versions or version == catalog_version:
                return catalog
    return None


def catalog_matches_id(catalog: Catalog, parsed: ParsedLibraryId) -> bool:
    return parsed.base_id == catalog.library.base_id


def rank_catalogs(catalogs: list[Catalog], query: str, library_name: str) -> list[Catalog]:
    query_tokens = normalize_tokens(query)
    name_tokens = normalize_tokens(library_name)
    ranked: list[tuple[int, str, Catalog]] = []
    for catalog in catalogs:
        library = catalog.library
        haystack = " ".join([library.title, library.description, *library.aliases]).lower()
        query_score = sum(1 for token in query_tokens if token in haystack)
        name_score = sum(1 for token in name_tokens if token in haystack)
        exact_score = 2 if library_name.lower() in haystack or query.lower() in haystack else 0
        score = query_score + name_score + exact_score
        if query_score > 0:
            ranked.append((score, library.id, catalog))
    return [catalog for _, _, catalog in sorted(ranked, key=lambda item: (-item[0], item[1]))]


def normalize_tokens(value: str) -> set[str]:
    return {
        token for token in value.lower().replace("/", " ").replace("@", " ").split() if token
    }


def catalog_to_library(catalog: Catalog) -> Library:
    library = catalog.library
    return Library(
        id=library.id,
        title=library.title,
        description=library.description,
        branch=library.source.branch,
        lastUpdateDate=library.state.last_update_date.isoformat(),
        state=LibraryState(library.state.status),
        totalTokens=0,
        totalSnippets=library.state.total_snippets,
        trustScore=10,
        benchmarkScore=95,
        versions=list(library.versions),
    )
