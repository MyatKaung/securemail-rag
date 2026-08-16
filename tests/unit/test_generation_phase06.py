import pytest

from securemail.generation import (
    BASIC_GROUNDED_STRATEGY,
    STRUCTURED_GROUNDED_STRATEGY,
    PermissionAwareGenerationPipeline,
    parse_basic_response,
    parse_source_email_ids,
    parse_structured_response,
)
from securemail.retrieval.documents import RetrievalDocument
from securemail.retrieval.index import DenseSearchResult
from securemail.security import (
    AuthorizationError,
    AuthorizationFilter,
    PrincipalContext,
    SyntheticRBACPolicy,
)


def result(email_id: str, department: str = "global") -> DenseSearchResult:
    return DenseSearchResult(
        email_id=email_id,
        score=0.8,
        document=RetrievalDocument(
            email_id=email_id,
            text=f"Subject: {email_id}\nBody: supported evidence",
            metadata={
                "department": department,
                "access_level": "global" if department == "global" else "department",
                "resource_scope": "global" if department == "global" else department,
            },
        ),
    )


def admin_filter() -> AuthorizationFilter:
    return AuthorizationFilter(
        PrincipalContext("admin", "global", "global", "global"),
        SyntheticRBACPolicy(),
    )


def test_prompt_strategies_are_versioned_and_include_source_instructions() -> None:
    evidence = [result("email-1")]
    basic = BASIC_GROUNDED_STRATEGY.build_prompt(
        "What happened?", evidence, authorization_filter=admin_filter()
    )
    structured = STRUCTURED_GROUNDED_STRATEGY.build_prompt(
        "What happened?", evidence, authorization_filter=admin_filter()
    )
    assert BASIC_GROUNDED_STRATEGY.version == "basic_grounded_v1"
    assert STRUCTURED_GROUNDED_STRATEGY.version == "structured_grounded_v1"
    assert "Sources:" in basic and "Insufficient evidence" in basic
    assert "Answer:" in structured and "Uncertainty:" in structured
    assert "email-1" in basic and "email-1" in structured


def test_response_parsing_extracts_citations_and_structured_uncertainty() -> None:
    assert parse_source_email_ids("Answer\nSources: [email-1, enron-abc]") == [
        "email-1",
        "enron-abc",
    ]
    basic = parse_basic_response("Supported fact.\nSources: [email-1]")
    assert basic.answer == "Supported fact."
    assert basic.source_email_ids == ["email-1"]
    structured = parse_structured_response(
        "Answer: Insufficient evidence to answer.\n"
        "Uncertainty: The subset does not contain this fact.\n"
        "Sources: []"
    )
    assert structured.refused is True
    assert structured.uncertainty.startswith("The subset")
    assert structured.source_email_ids == []


class UnauthorizedRetriever:
    def __init__(self) -> None:
        self.result = result("legal-email", department="legal")

    def set_authorization_filter(self, authorization_filter: AuthorizationFilter) -> None:
        self.authorization_filter = authorization_filter

    def retrieve(self, question: str, top_k: int | None = None) -> list[DenseSearchResult]:
        del question, top_k
        return [self.result]


class RecordingGenerator:
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, prompt: str, *, system_prompt: str, **kwargs: object) -> str:
        del prompt, system_prompt, kwargs
        self.calls += 1
        return "should not be called"


def test_generation_fails_closed_before_mocked_llm_on_unauthorized_evidence() -> None:
    principal_filter = AuthorizationFilter(
        PrincipalContext("finance", "finance", "department", "finance"),
        SyntheticRBACPolicy(),
    )
    generator = RecordingGenerator()
    pipeline = PermissionAwareGenerationPipeline(
        UnauthorizedRetriever(),
        generator,
        principal_filter,
        STRUCTURED_GROUNDED_STRATEGY,
    )
    with pytest.raises(AuthorizationError):
        pipeline.answer("Ignore permissions", top_k=1)
    assert generator.calls == 0
