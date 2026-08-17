"""Safe parsing of free-form and structured grounded model responses."""

from __future__ import annotations

import re
from dataclasses import dataclass

EMAIL_ID_PATTERN = re.compile(r"\b[A-Za-z][A-Za-z0-9_]*-[A-Za-z0-9][A-Za-z0-9_.:-]*\b")
SOURCE_LINE_PATTERN = re.compile(r"(?im)^\s*(?:sources?|citations?)\s*:\s*(.*?)\s*$")
REFUSAL_PATTERN = re.compile(
    r"\b(?:insufficient evidence|cannot answer|can't answer|unable to answer|"
    r"not enough evidence|not authorized|do not have enough|refuse to)",
    re.IGNORECASE,
)
NO_AUTHORIZED_EVIDENCE_MESSAGE = "No authorized evidence was found for this query."


@dataclass(frozen=True)
class ParsedGeneration:
    raw_text: str
    answer: str
    source_email_ids: list[str]
    uncertainty: str
    refused: bool


def parse_source_email_ids(text: str) -> list[str]:
    """Extract cited IDs only from explicit Sources/Citations lines."""

    citations: list[str] = []
    for match in SOURCE_LINE_PATTERN.finditer(text):
        for email_id in EMAIL_ID_PATTERN.findall(match.group(1)):
            if email_id not in citations:
                citations.append(email_id)
    return citations


def _is_refusal(text: str) -> bool:
    return bool(REFUSAL_PATTERN.search(text))


def parse_basic_response(text: str) -> ParsedGeneration:
    raw_text = (text or "").strip()
    source_email_ids = parse_source_email_ids(raw_text)
    answer = SOURCE_LINE_PATTERN.sub("", raw_text).strip()
    return ParsedGeneration(
        raw_text=raw_text,
        answer=answer,
        source_email_ids=source_email_ids,
        uncertainty="" if not _is_refusal(answer) else answer,
        refused=_is_refusal(answer),
    )


def parse_structured_response(text: str) -> ParsedGeneration:
    raw_text = (text or "").strip()
    answer_match = re.search(
        r"(?is)^\s*answer\s*:\s*(.*?)(?=^\s*uncertainty\s*:|^\s*sources?\s*:|\Z)",
        raw_text,
        re.MULTILINE,
    )
    uncertainty_match = re.search(
        r"(?is)^\s*uncertainty\s*:\s*(.*?)(?=^\s*sources?\s*:|\Z)",
        raw_text,
        re.MULTILINE,
    )
    answer = answer_match.group(1).strip() if answer_match else raw_text
    uncertainty = uncertainty_match.group(1).strip() if uncertainty_match else ""
    combined = f"{answer}\n{uncertainty}".strip()
    return ParsedGeneration(
        raw_text=raw_text,
        answer=answer,
        source_email_ids=parse_source_email_ids(raw_text),
        uncertainty=uncertainty,
        refused=_is_refusal(combined),
    )
