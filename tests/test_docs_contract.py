import re
from pathlib import Path
from typing import Final

README_PATH: Final = Path("README.md")
REQUIRED_README_STRINGS: Final = (
    "CONTEXT7_API_URL=http://localhost:8000/api",
    "SDK-compatible means backend wire contract compatible only",
    "X-Context7-Auth-Prompt",
)
REQUIRED_DOCS: Final = (
    "docs/architecture.md",
    "docs/api.md",
    "docs/ingestion.md",
    "docs/catalog.md",
    "docs/retrieval.md",
    "docs/configuration.md",
    "docs/auth.md",
    "docs/deployment.md",
    "docs/development.md",
    "docs/testing.md",
    "docs/troubleshooting.md",
)
DOC_SOURCE_MARKERS: Final = {
    "docs/architecture.md": ("app/routes.py", "app/main.py", "app/formatters.py", "app/retrieval"),
    "docs/api.md": ("/healthz", "/api/v2/libs/search", "/api/v2/context", "app/routes.py"),
    "docs/ingestion.md": ("app/cli.py", "app/ingest/parser.py", "app/store.py"),
    "docs/catalog.md": ("libraries/*.yaml", "app/catalog.py"),
    "docs/retrieval.md": (
        "app/retrieval/lexical.py",
        "app/retrieval/qdrant.py",
        "app/embeddings.py",
    ),
    "docs/configuration.md": (".env.example", "app/settings.py", "DOCS_API_KEYS"),
    "docs/auth.md": ("app/auth.py", "secrets.compare_digest", "/healthz"),
    "docs/deployment.md": ("Dockerfile", "docker-compose.yml", "127.0.0.1:8000"),
    "docs/development.md": (
        "pyproject.toml",
        "uv run ruff check app tests",
        "uv run basedpyright app tests",
    ),
    "docs/testing.md": ("scripts/qa_http_contract.sh", "scripts/qa_mcp_contract.sh"),
    "docs/troubleshooting.md": ("401", "Qdrant", "symlink"),
}
README_DOC_LINK_RE: Final = re.compile(r"\]\((docs/[^)#\s]+\.md)(?:#[^)]+)?\)")


def read_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def readme_doc_links() -> set[str]:
    readme = README_PATH.read_text(encoding="utf-8")
    return set(README_DOC_LINK_RE.findall(readme))


def test_readme_documents_required_contract_strings() -> None:
    text = README_PATH.read_text(encoding="utf-8")

    for contract_string in REQUIRED_README_STRINGS:
        assert contract_string in text


def test_required_docs_files_exist() -> None:
    missing = [doc_path for doc_path in REQUIRED_DOCS if not Path(doc_path).is_file()]

    assert missing == []


def test_docs_name_their_source_of_truth_markers() -> None:
    missing = {
        doc_path: [marker for marker in markers if marker not in read_text(doc_path)]
        for doc_path, markers in DOC_SOURCE_MARKERS.items()
        if Path(doc_path).is_file()
    }

    assert {doc_path: markers for doc_path, markers in missing.items() if markers} == {}


def test_readme_links_to_required_docs() -> None:
    links = readme_doc_links()

    assert set(REQUIRED_DOCS).issubset(links)


def test_readme_docs_links_resolve_to_files() -> None:
    missing = [link for link in sorted(readme_doc_links()) if not Path(link).is_file()]

    assert missing == []
