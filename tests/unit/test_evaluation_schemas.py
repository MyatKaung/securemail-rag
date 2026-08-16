from pathlib import Path

import pytest
from pydantic import ValidationError

from securemail.evaluation import (
    GenerationEvaluationRecord,
    PermissionTestRecord,
    RetrievalGroundTruthRecord,
    load_records,
)

ROOT = Path(__file__).resolve().parents[2]


def test_phase_00_sample_datasets_match_their_contracts():
    retrieval = load_records(
        ROOT / "evals/datasets/retrieval_ground_truth.sample.json",
        RetrievalGroundTruthRecord,
    )
    permissions = load_records(
        ROOT / "evals/datasets/permission_tests.sample.json",
        PermissionTestRecord,
    )
    generation = load_records(
        ROOT / "evals/datasets/generation_tests.sample.json",
        GenerationEvaluationRecord,
    )

    assert retrieval[0].id == "ret-001"
    assert permissions[0].expected == "deny"
    assert generation[0].must_refuse_if_insufficient is True


def test_permission_records_reject_unknown_decisions():
    with pytest.raises(ValidationError):
        PermissionTestRecord.model_validate(
            {
                "id": "perm-001",
                "principal": {"role": "finance", "department": "finance"},
                "question": "Can I see this?",
                "expected": "maybe",
            }
        )


def test_retrieval_records_reject_duplicate_relevant_ids():
    with pytest.raises(ValidationError, match="duplicates"):
        RetrievalGroundTruthRecord.model_validate(
            {
                "id": "ret-001",
                "question": "What happened?",
                "relevant_email_ids": ["email-1", "email-1"],
            }
        )
