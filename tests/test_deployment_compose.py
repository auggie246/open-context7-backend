from pathlib import Path
from typing import ClassVar, Final

import yaml
from pydantic import BaseModel, ConfigDict, Field

COMPOSE_PATH: Final = Path("docker-compose.yml")
DOCKERFILE_PATH: Final = Path("Dockerfile")
EXPECTED_QDRANT_URL: Final = "http://qdrant:6333"
EXPECTED_QDRANT_IMAGE: Final = "qdrant/qdrant:v1.12.6"
EXPECTED_QDRANT_VOLUME: Final = "qdrant-data:/qdrant/storage"
EXPECTED_DOCKERFILE_CMD: Final = (
    'CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]'
)


class ComposeService(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow", frozen=True)

    build: str | None = None
    environment: dict[str, str] = Field(default_factory=dict)
    image: str | None = None
    volumes: tuple[str, ...] = ()


class ComposeFile(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow", frozen=True)

    services: dict[str, ComposeService]
    volumes: dict[str, None] = Field(default_factory=dict)


def test_compose_keeps_qdrant_as_separate_service_from_docs_api_image() -> None:
    # Given
    compose = ComposeFile.model_validate(yaml.safe_load(COMPOSE_PATH.read_text()))
    dockerfile_lines = DOCKERFILE_PATH.read_text().splitlines()

    # When
    docs_api = compose.services["docs-api"]
    qdrant = compose.services["qdrant"]

    # Then
    assert docs_api.build == "."
    assert docs_api.environment["DOCS_QDRANT_URL"] == EXPECTED_QDRANT_URL
    assert qdrant.image == EXPECTED_QDRANT_IMAGE
    assert EXPECTED_QDRANT_VOLUME in qdrant.volumes
    assert "qdrant-data" in compose.volumes
    assert dockerfile_lines[-1] == EXPECTED_DOCKERFILE_CMD
    assert all("qdrant" not in line.casefold() for line in dockerfile_lines)
