"""Validated request and response contracts for the application interface."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PrincipalRequest(BaseModel):
    """Explicit synthetic principal context supplied by the caller."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    role: str = Field(min_length=1, max_length=64)
    department: str = Field(min_length=1, max_length=64)
    access_level: str = Field(min_length=1, max_length=32)
    resource_scope: str = Field(min_length=1, max_length=64)


class QueryRequest(BaseModel):
    """End-to-end secure RAG request."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    question: str = Field(min_length=1, max_length=4000)
    principal: PrincipalRequest


class QueryResponse(BaseModel):
    """Authorization-safe response; email bodies are intentionally excluded."""

    request_id: str
    answer: str
    source_email_ids: list[str]
    retrieval_method: str
    retrieved_evidence_count: int = Field(ge=0)
    refused: bool
    insufficient_evidence: bool
    uncertainty: str = ""


class FeedbackRequest(BaseModel):
    """User feedback tied to an existing request correlation ID."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    request_id: str = Field(
        min_length=1, max_length=64, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$"
    )
    positive: bool
    comment: str | None = Field(default=None, max_length=500)


class FeedbackResponse(BaseModel):
    request_id: str
    recorded: bool


DEMO_PRINCIPALS: dict[str, PrincipalRequest] = {
    "Finance employee": PrincipalRequest(
        role="employee",
        department="finance",
        access_level="department",
        resource_scope="finance",
    ),
    "Legal employee": PrincipalRequest(
        role="employee",
        department="legal",
        access_level="department",
        resource_scope="legal",
    ),
    "Shared/general employee": PrincipalRequest(
        role="employee",
        department="general",
        access_level="standard",
        resource_scope="shared",
    ),
    "Admin": PrincipalRequest(
        role="admin",
        department="global",
        access_level="global",
        resource_scope="global",
    ),
}
