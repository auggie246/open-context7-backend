from datetime import UTC, datetime
from enum import StrEnum
from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field

type ResponseType = Literal["json", "txt"]
type ResponseMediaType = Literal["application/json", "text/plain"]


class WireModel(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)


class HealthResponse(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    status: Literal["ok"] = "ok"
    service: str = "open-context7-backend"
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class LibraryState(StrEnum):
    FINALIZED = "finalized"
    INITIAL = "initial"
    PROCESSING = "processing"
    ERROR = "error"
    DELETE = "delete"


class Library(WireModel):
    id: str | None = None
    title: str | None = None
    description: str | None = None
    branch: str | None = None
    lastUpdateDate: str | None = None  # noqa: N815 - OpenAPI wire field
    state: LibraryState | None = None
    totalTokens: int | None = None  # noqa: N815 - OpenAPI wire field
    totalSnippets: int | None = None  # noqa: N815 - OpenAPI wire field
    stars: int | None = None
    trustScore: int | None = Field(default=None, ge=0, le=10)  # noqa: N815
    benchmarkScore: float | None = Field(default=None, ge=0, le=100)  # noqa: N815
    versions: list[str] | None = None


class SearchResponse(WireModel):
    results: list[Library]
    searchFilterApplied: bool = False  # noqa: N815 - OpenAPI wire field


class CodeExample(WireModel):
    language: str
    code: str


class CodeSnippet(WireModel):
    codeTitle: str  # noqa: N815 - OpenAPI wire field
    codeDescription: str  # noqa: N815 - OpenAPI wire field
    codeLanguage: str  # noqa: N815 - OpenAPI wire field
    codeTokens: int  # noqa: N815 - OpenAPI wire field
    codeId: str  # noqa: N815 - OpenAPI wire field
    pageTitle: str  # noqa: N815 - OpenAPI wire field
    codeList: list[CodeExample]  # noqa: N815 - OpenAPI wire field
    isDynamic: bool | None = None  # noqa: N815 - OpenAPI wire field
    sourceFile: str | None = None  # noqa: N815 - OpenAPI wire field


class InfoSnippet(WireModel):
    content: str
    contentTokens: int  # noqa: N815 - OpenAPI wire field
    pageId: str | None = None  # noqa: N815 - OpenAPI wire field
    breadcrumb: str | None = None


class ContextResponse(WireModel):
    codeSnippets: list[CodeSnippet]  # noqa: N815 - OpenAPI wire field
    infoSnippets: list[InfoSnippet]  # noqa: N815 - OpenAPI wire field


class ErrorBody(WireModel):
    error: str
    message: str


def response_media_type(response_type: ResponseType | None) -> ResponseMediaType:
    match response_type:
        case None | "txt":
            return "text/plain"
        case "json":
            return "application/json"
