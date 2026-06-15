from functools import lru_cache
from typing import Annotated, ClassVar, Final, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

DEFAULT_QDRANT_URL: Final = "http://localhost:6333"


class Settings(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        env_nested_delimiter="__",
        env_prefix="DOCS_",
    )

    api_keys: Annotated[list[str], NoDecode] = Field(default_factory=list)
    qdrant_url: str = DEFAULT_QDRANT_URL
    retrieval_mode: Literal["lexical", "qdrant"] = "lexical"
    embedding_mode: str = "deterministic"
    max_context_tokens: int = 5000
    reranker_enabled: bool = False

    @field_validator("api_keys", mode="before")
    @classmethod
    def parse_api_keys(cls, raw: str | list[str]) -> list[str]:
        match raw:
            case str():
                return [key for item in raw.split(",") if (key := item.strip())]
            case list():
                return raw


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
