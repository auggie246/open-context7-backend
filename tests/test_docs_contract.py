from pathlib import Path


def test_readme_documents_required_contract_strings() -> None:
    text = Path("README.md").read_text(encoding="utf-8")

    assert "CONTEXT7_API_URL=http://localhost:8000/api" in text
    assert "SDK-compatible means backend wire contract compatible only" in text
    assert "X-Context7-Auth-Prompt" in text
