import json
import re
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import ClassVar, Literal, cast

import yaml
from pydantic import BaseModel, ConfigDict, Field

LIBRARY_ID_PATTERN = re.compile(r"^/[^/]+/[^/@]+(?:/[^/]+|@[^/]+)?$")
VERSIONED_PART_COUNT = 3
type JsonValue = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]


class CatalogValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ParsedLibraryId:
    raw: str
    base_id: str
    version: str | None
    version_style: Literal["/", "@"] | None


class CatalogModel(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)


class CatalogSource(CatalogModel):
    type: Literal["dir"]
    directory: Path
    branch: str = "main"
    include: tuple[str, ...] = ("**/*.md", "**/*.mdx")
    exclude: tuple[str, ...] = ()


class CatalogState(CatalogModel):
    status: Literal["finalized", "initial", "processing", "error", "delete"] = "initial"
    total_snippets: int = Field(default=0, alias="totalSnippets")
    last_update_date: date = Field(alias="lastUpdateDate")


class CatalogLibrary(CatalogModel):
    id: str
    title: str
    description: str
    aliases: tuple[str, ...] = ()
    versions: tuple[str, ...] = ()
    source: CatalogSource
    state: CatalogState
    base_id: str
    version: str | None


class Catalog(CatalogModel):
    library: CatalogLibrary


class CatalogFile(CatalogModel):
    id: str
    title: str
    description: str
    aliases: tuple[str, ...] = ()
    versions: tuple[str, ...] = ()
    source: CatalogSource
    state: CatalogState


def parse_library_id(library_id: str) -> ParsedLibraryId:
    if LIBRARY_ID_PATTERN.fullmatch(library_id) is None:
        msg = f"invalid library id: {library_id}"
        raise CatalogValidationError(msg)
    if "@" in library_id:
        base_id, version = library_id.split("@", maxsplit=1)
        return ParsedLibraryId(
            raw=library_id,
            base_id=base_id,
            version=version,
            version_style="@",
        )
    parts = library_id.strip("/").split("/")
    if len(parts) == VERSIONED_PART_COUNT:
        return ParsedLibraryId(
            raw=library_id,
            base_id=f"/{parts[0]}/{parts[1]}",
            version=parts[2],
            version_style="/",
        )
    return ParsedLibraryId(raw=library_id, base_id=library_id, version=None, version_style=None)


def load_catalog(path: Path) -> Catalog:
    try:
        raw_data = cast("object", yaml.safe_load(path.read_text(encoding="utf-8")))
        file_model = CatalogFile.model_validate(raw_data)
        parsed_id = parse_library_id(file_model.id)
    except (OSError, ValueError, TypeError) as error:
        msg = f"invalid catalog file {path}: {error}"
        raise CatalogValidationError(msg) from error
    return Catalog(
        library=CatalogLibrary(
            id=file_model.id,
            title=file_model.title,
            description=file_model.description,
            aliases=file_model.aliases,
            versions=file_model.versions,
            source=file_model.source,
            state=file_model.state,
            base_id=parsed_id.base_id,
            version=parsed_id.version,
        )
    )


def _catalog_to_wire(catalog: Catalog) -> Mapping[str, JsonValue]:
    library = catalog.library
    return {
        "id": library.id,
        "baseId": library.base_id,
        "version": library.version or "",
        "title": library.title,
        "description": library.description,
        "aliases": list(library.aliases),
        "versions": list(library.versions),
        "source": {
            "type": library.source.type,
            "directory": library.source.directory.as_posix(),
            "branch": library.source.branch,
            "include": list(library.source.include),
            "exclude": list(library.source.exclude),
        },
        "state": {
            "status": library.state.status,
            "totalSnippets": library.state.total_snippets,
            "lastUpdateDate": library.state.last_update_date.isoformat(),
        },
    }


def main() -> None:
    catalog = load_catalog(Path(sys.argv[1]))
    print(json.dumps(_catalog_to_wire(catalog), sort_keys=True))


if __name__ == "__main__":
    main()
