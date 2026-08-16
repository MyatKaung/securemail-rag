from pathlib import Path

from securemail.evaluation import GenerationEvaluationRecord, load_records
from securemail.retrieval.indexing import load_normalized_jsonl


def test_generation_dataset_is_grounded_and_covers_required_case_types() -> None:
    root = Path(__file__).resolve().parents[2]
    corpus_ids = {
        record.email_id
        for record in load_normalized_jsonl(root / "data/sample/enron_dev_500.jsonl")
    }
    cases = load_records(
        root / "evals/datasets/generation_ground_truth.phase06.json",
        GenerationEvaluationRecord,
    )

    assert len(cases) == 20
    assert all(
        set(case.expected_source_ids + case.restricted_email_ids) <= corpus_ids for case in cases
    )
    assert {
        "direct_fact",
        "multi_email_synthesis",
        "insufficient_evidence",
        "permission_sensitive",
        "adversarial_prompt_override",
        "adversarial_identity_claim",
        "adversarial_transformation_request",
    } <= {case.case_type for case in cases}
    assert sum(not case.sufficient_evidence for case in cases) >= 6
