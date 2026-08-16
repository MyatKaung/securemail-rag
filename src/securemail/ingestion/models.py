"""Normalized Enron email records produced by Phase 01."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class NormalizedEmail(BaseModel):
    """Stable, JSON-serializable representation of one email message."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    email_id: str = Field(min_length=1)
    message_id: str | None = None
    sender: str = ""
    recipients_to: list[str] = Field(default_factory=list)
    recipients_cc: list[str] = Field(default_factory=list)
    recipients_bcc: list[str] = Field(default_factory=list)
    sent_at: str | None = None
    subject: str = ""
    body: str = ""
    mailbox: str = ""
    source_path: str = Field(min_length=1)

    # These fields are an explicitly synthetic experiment overlay. They are
    # not historical Enron permissions.
    synthetic_role: str = Field(min_length=1)
    department: str = Field(min_length=1)
    access_level: str = Field(min_length=1)
    resource_scope: str = Field(min_length=1)
