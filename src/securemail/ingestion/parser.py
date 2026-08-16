"""Parsing and normalization for RFC 2822/MIME Enron messages."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable
from datetime import UTC
from email import policy
from email.header import decode_header, make_header
from email.message import EmailMessage, Message
from email.parser import BytesParser
from email.utils import getaddresses, parsedate_to_datetime
from pathlib import PurePosixPath

from .models import NormalizedEmail
from .rbac import assign_synthetic_rbac

_WHITESPACE_RE = re.compile(r"[ \t]+")


def _decode_header(value: str | None) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value))).strip()
    except (LookupError, UnicodeError, ValueError):
        return value.strip()


def _normalize_message_id(value: str | None) -> str | None:
    decoded = _decode_header(value)
    if not decoded:
        return None
    return _WHITESPACE_RE.sub("", decoded).casefold()


def _normalize_addresses(values: Iterable[str]) -> list[str]:
    addresses: list[str] = []
    for _, address in getaddresses(list(values)):
        normalized = address.strip().casefold()
        if normalized:
            addresses.append(normalized)
    if addresses:
        return list(dict.fromkeys(addresses))
    fallback = [value.strip().casefold() for value in values if value.strip()]
    return list(dict.fromkeys(fallback))


def _normalize_date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _decode_payload(part: Message) -> str:
    try:
        payload = part.get_payload(decode=True)
    except (LookupError, UnicodeError, ValueError):
        payload = None
    if isinstance(payload, bytes):
        charset = part.get_content_charset() or "utf-8"
        return payload.decode(charset, errors="replace")
    if isinstance(payload, str):
        return payload
    raw_payload = part.get_payload()
    return raw_payload if isinstance(raw_payload, str) else ""


def _extract_body(message: Message) -> str:
    plain_parts: list[str] = []
    html_parts: list[str] = []
    parts = message.walk() if message.is_multipart() else [message]
    for part in parts:
        if part.is_multipart() or part.get_content_disposition() == "attachment":
            continue
        content_type = part.get_content_type()
        if content_type == "text/plain":
            plain_parts.append(_decode_payload(part))
        elif content_type == "text/html":
            html_parts.append(_decode_payload(part))
    body = "\n\n".join(part for part in plain_parts if part.strip())
    if not body:
        body = "\n\n".join(part for part in html_parts if part.strip())
    return body.replace("\r\n", "\n").replace("\r", "\n").strip()


def mailbox_from_source_path(source_path: str) -> str:
    """Extract the mailbox component from an archive or maildir path."""

    parts = PurePosixPath(source_path.replace("\\", "/")).parts
    try:
        return parts[parts.index("maildir") + 1]
    except (ValueError, IndexError):
        return parts[0] if parts else "unknown"


def _stable_id(
    message_id: str | None,
    sender: str,
    recipients_to: list[str],
    recipients_cc: list[str],
    recipients_bcc: list[str],
    sent_at: str | None,
    subject: str,
    body: str,
) -> str:
    if message_id:
        identity = {"message_id": message_id}
    else:
        identity = {
            "sender": sender,
            "recipients_to": recipients_to,
            "recipients_cc": recipients_cc,
            "recipients_bcc": recipients_bcc,
            "sent_at": sent_at,
            "subject": subject,
            "body": body,
        }
    digest = hashlib.sha256(
        json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()
    return f"enron-{digest}"


def normalize_message(raw_bytes: bytes, source_path: str) -> NormalizedEmail:
    """Parse one raw message, tolerating missing or malformed headers."""

    try:
        message: EmailMessage = BytesParser(policy=policy.default).parsebytes(raw_bytes)
    except (LookupError, UnicodeError, ValueError):
        message = EmailMessage(policy=policy.default)
        message.set_payload(raw_bytes.decode("utf-8", errors="replace"))

    message_id = _normalize_message_id(message.get("Message-ID"))
    sender_values = _normalize_addresses(message.get_all("From", []))
    sender = sender_values[0] if sender_values else ""
    recipients_to = _normalize_addresses(message.get_all("To", []))
    recipients_cc = _normalize_addresses(message.get_all("Cc", []))
    recipients_bcc = _normalize_addresses(message.get_all("Bcc", []))
    sent_at = _normalize_date(message.get("Date"))
    subject = _decode_header(message.get("Subject"))
    body = _extract_body(message)
    mailbox = mailbox_from_source_path(source_path)
    rbac = assign_synthetic_rbac(mailbox)

    return NormalizedEmail(
        email_id=_stable_id(
            message_id,
            sender,
            recipients_to,
            recipients_cc,
            recipients_bcc,
            sent_at,
            subject,
            body,
        ),
        message_id=message_id,
        sender=sender,
        recipients_to=recipients_to,
        recipients_cc=recipients_cc,
        recipients_bcc=recipients_bcc,
        sent_at=sent_at,
        subject=subject,
        body=body,
        mailbox=mailbox,
        source_path=source_path.replace("\\", "/"),
        synthetic_role=rbac.synthetic_role,
        department=rbac.department,
        access_level=rbac.access_level,
        resource_scope=rbac.resource_scope,
    )
