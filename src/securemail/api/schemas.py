"""Validated request and response contracts for the application interface."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class QueryRequest(BaseModel):
    """End-to-end secure RAG request using the authenticated demo session."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    question: str = Field(min_length=1, max_length=4000)


class LoginRequest(BaseModel):
    """Synthetic demo login credentials; never includes principal metadata."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    email: str = Field(min_length=1, max_length=320)
    password: str = Field(min_length=1, max_length=128)


class LoginResponse(BaseModel):
    """Safe display information for the authenticated synthetic identity."""

    email: str
    department: str
    role: str


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
