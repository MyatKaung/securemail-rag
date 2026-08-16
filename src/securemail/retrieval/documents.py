"""Document preparation for the dense baseline."""

from __future__ import annotations

from dataclasses import dataclass

from securemail.ingestion import NormalizedEmail


@dataclass(frozen=True)
class RetrievalDocument:
    """One retrievable document while preserving the source email identity."""

    email_id: str
    text: str
    metadata: dict[str, str | None]


def prepare_document(email: NormalizedEmail, max_chars: int = 12_000) -> RetrievalDocument:
    """Represent one normalized email as a single dense-retrieval document."""

    if max_chars <= 0:
        raise ValueError("max_chars must be greater than zero")
    header_lines = [
        f"Subject: {email.subject}",
        f"From: {email.sender}",
        f"To: {', '.join(email.recipients_to)}",
        f"Cc: {', '.join(email.recipients_cc)}",
        f"Date: {email.sent_at or ''}",
        "Body:",
        email.body,
    ]
    text = "\n".join(header_lines).strip()
    return RetrievalDocument(
        email_id=email.email_id,
        text=text[:max_chars],
        metadata={
            "subject": email.subject,
            "sender": email.sender,
            "sent_at": email.sent_at,
            "mailbox": email.mailbox,
            "source_path": email.source_path,
            "synthetic_role": email.synthetic_role,
            "department": email.department,
            "access_level": email.access_level,
            "resource_scope": email.resource_scope,
        },
    )


def prepare_documents(
    emails: list[NormalizedEmail], max_chars: int = 12_000
) -> list[RetrievalDocument]:
    """Prepare documents in input order for deterministic indexing."""

    return [prepare_document(email, max_chars=max_chars) for email in emails]
