"""Pydantic contracts for evaluation datasets.

These schemas deliberately describe records only. Retrieval, authorization,
and generation behavior are implemented in later phases.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EvaluationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(min_length=1)
    question: str = Field(min_length=1)


class RetrievalGroundTruthRecord(EvaluationRecord):
    relevant_email_ids: list[str] = Field(min_length=1)
    notes: str = ""

    @field_validator("relevant_email_ids")
    @classmethod
    def unique_email_ids(cls, value: list[str]) -> list[str]:
        if any(not email_id.strip() for email_id in value):
            raise ValueError("relevant_email_ids must contain non-empty IDs")
        if len(value) != len(set(value)):
            raise ValueError("relevant_email_ids must not contain duplicates")
        return value


class Principal(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    role: str = Field(min_length=1)
    department: str = Field(min_length=1)
    access_level: str = "standard"
    resource_scope: str = "shared"


class PermissionTestRecord(EvaluationRecord):
    principal: Principal
    allowed_email_ids: list[str] = Field(default_factory=list)
    forbidden_email_ids: list[str] = Field(default_factory=list)
    expected: Literal["allow", "deny"]
    case_type: str = "unspecified"
    notes: str = ""

    @field_validator("allowed_email_ids", "forbidden_email_ids")
    @classmethod
    def valid_email_ids(cls, value: list[str]) -> list[str]:
        if any(not email_id.strip() for email_id in value):
            raise ValueError("email ID lists must contain non-empty IDs")
        if len(value) != len(set(value)):
            raise ValueError("email ID lists must not contain duplicates")
        return value


class GenerationEvaluationRecord(EvaluationRecord):
    expected_source_ids: list[str] = Field(default_factory=list)
    must_refuse_if_insufficient: bool = True
    expected_answer_terms: list[str] = Field(default_factory=list)
    sufficient_evidence: bool = True
    principal: Principal = Field(
        default_factory=lambda: Principal(
            role="admin",
            department="global",
            access_level="global",
            resource_scope="global",
        )
    )
    restricted_email_ids: list[str] = Field(default_factory=list)
    case_type: str = "direct_fact"
    notes: str = ""


RecordT = TypeVar("RecordT", bound=BaseModel)


def load_records(path: str | Path, record_type: type[RecordT]) -> list[RecordT]:
    """Load a JSON array and validate every item against ``record_type``."""

    dataset_path = Path(path)
    try:
        with dataset_path.open(encoding="utf-8") as handle:
            raw: Any = json.load(handle)
    except OSError as exc:
        raise ValueError(f"Unable to read evaluation dataset: {dataset_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in evaluation dataset: {dataset_path}") from exc

    if not isinstance(raw, list):
        raise TypeError(f"Evaluation dataset must be a JSON array: {dataset_path}")
    return [record_type.model_validate(item) for item in raw]
