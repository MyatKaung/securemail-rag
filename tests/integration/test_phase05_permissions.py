from pathlib import Path

from securemail.evaluation import PermissionTestRecord, load_records
from securemail.retrieval.indexing import load_normalized_jsonl
from securemail.security import PrincipalContext, SyntheticRBACPolicy


def test_permission_dataset_is_grounded_in_current_corpus_and_covers_required_cases() -> None:
    root = Path(__file__).resolve().parents[2]
    records = load_normalized_jsonl(root / "data/sample/enron_dev_500.jsonl")
    corpus_ids = {record.email_id for record in records}
    cases = load_records(
        root / "evals/datasets/permission_ground_truth.phase05.json",
        PermissionTestRecord,
    )

    assert len(records) == 500
    assert len(cases) == 24
    assert all(
        set(case.allowed_email_ids + case.forbidden_email_ids) <= corpus_ids for case in cases
    )
    assert {case.expected for case in cases} == {"allow", "deny"}
    assert {
        "authorized_same_department",
        "cross_department_denied",
        "higher_access_level",
        "lower_access_level",
        "shared_scope_denied",
        "admin_global_access",
        "adversarial_prompt_override",
        "adversarial_identity_claim",
        "adversarial_encoding_request",
        "adversarial_indirect_summary",
    } <= {case.case_type for case in cases}


def test_synthetic_policy_accepts_explicit_principal_context() -> None:
    principal = PrincipalContext(
        role="admin",
        department="global",
        access_level="global",
        resource_scope="global",
    )
    assert SyntheticRBACPolicy().is_allowed(
        principal,
        {
            "department": "global",
            "access_level": "global",
            "resource_scope": "global",
        },
    )
