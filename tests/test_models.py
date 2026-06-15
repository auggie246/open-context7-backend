import pytest
from app.models import (
    CodeExample,
    CodeSnippet,
    ContextResponse,
    ErrorBody,
    InfoSnippet,
    SearchResponse,
    response_media_type,
)
from pydantic import ValidationError


def test_search_response_defaults_filter_flag_when_omitted() -> None:
    # Given: a minimal Context7 search payload without the filter flag.
    response = SearchResponse(results=[])

    # When: the response is serialized for the wire.
    payload = response.model_dump()

    # Then: Context7's required filter field is present and false.
    assert payload == {"results": [], "searchFilterApplied": False}


def test_context_response_schema_requires_snippet_arrays() -> None:
    assert ContextResponse.model_fields["codeSnippets"].is_required()
    assert ContextResponse.model_fields["infoSnippets"].is_required()


def test_context_response_accepts_required_code_and_info_shapes() -> None:
    # Given: a complete JSON context response payload.
    response = ContextResponse(
        codeSnippets=[
            CodeSnippet(
                codeTitle="Install",
                codeDescription="Install the package.",
                codeLanguage="bash",
                codeTokens=4,
                codeId="/docs/install.md#L1-L2",
                pageTitle="Install guide",
                codeList=[CodeExample(language="bash", code="uv sync")],
            )
        ],
        infoSnippets=[
            InfoSnippet(
                content="Use the documented install path.",
                contentTokens=6,
                pageId="/docs/install.md",
                breadcrumb="Docs > Install",
            )
        ],
    )

    # When: the response is serialized.
    payload = response.model_dump()

    # Then: required OpenAPI fields are emitted with wire names.
    assert payload["codeSnippets"][0]["codeList"] == [{"language": "bash", "code": "uv sync"}]
    assert payload["infoSnippets"][0]["contentTokens"] == 6


def test_required_snippet_fields_reject_incomplete_payloads() -> None:
    with pytest.raises(ValidationError, match="code"):
        _ = CodeExample.model_validate({"language": "bash"})


def test_response_type_matrix_defaults_to_text_for_mcp() -> None:
    # Given/When/Then: omitted and txt response types are plain text; json is JSON.
    assert response_media_type(None) == "text/plain"
    assert response_media_type("txt") == "text/plain"
    assert response_media_type("json") == "application/json"


def test_error_body_uses_context7_error_shape() -> None:
    # Given: a standard Context7 error body.
    error = ErrorBody(error="unauthorized", message="Bearer token required")

    # When/Then: it serializes to the documented shape.
    assert error.model_dump() == {
        "error": "unauthorized",
        "message": "Bearer token required",
    }
