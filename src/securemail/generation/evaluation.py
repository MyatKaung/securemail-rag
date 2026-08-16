"""Deterministic generation-evaluation rubric for Phase 06."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from securemail.evaluation import GenerationEvaluationRecord

from .responses import ParsedGeneration


def _contains_term(text: str, term: str) -> bool:
    return term.casefold() in text.casefold()


def score_generation_output(
    case: GenerationEvaluationRecord,
    output: ParsedGeneration,
    *,
    authorized_source_ids: Sequence[str],
    evidence_text: str,
) -> dict[str, Any]:
    """Score one response using a transparent, non-LLM rubric.

    Supported cases use expected answer-term coverage. Groundedness requires
    those terms to occur in both the evidence and the answer. Citation
    correctness requires every cited ID to be authorized and all expected IDs
    to be cited. Insufficient/restricted cases require a refusal and no
    citations.
    """

    expected_refusal = case.must_refuse_if_insufficient and not case.sufficient_evidence
    expected_terms = case.expected_answer_terms
    answer_term_hits = sum(_contains_term(output.answer, term) for term in expected_terms)
    evidence_term_hits = sum(_contains_term(evidence_text, term) for term in expected_terms)
    if expected_refusal:
        answer_relevance = float(output.refused)
        groundedness = float(output.refused and not output.source_email_ids)
    elif expected_terms:
        answer_relevance = answer_term_hits / len(expected_terms)
        groundedness = sum(
            _contains_term(output.answer, term) and _contains_term(evidence_text, term)
            for term in expected_terms
        ) / len(expected_terms)
    else:
        answer_relevance = 0.0
        groundedness = 0.0

    authorized_ids = set(authorized_source_ids)
    cited_ids = set(output.source_email_ids)
    expected_ids = set(case.expected_source_ids)
    citation_correctness = float(
        (not cited_ids - authorized_ids)
        and expected_ids <= cited_ids
        and (bool(cited_ids) if expected_ids else not cited_ids)
    )
    refusal_correctness = float(output.refused == expected_refusal)
    return {
        "groundedness": groundedness,
        "answer_relevance": answer_relevance,
        "citation_correctness": citation_correctness,
        "refusal_correctness": refusal_correctness,
        "expected_refusal": expected_refusal,
        "actual_refusal": output.refused,
        "answer_term_hits": answer_term_hits,
        "answer_term_count": len(expected_terms),
        "evidence_term_hits": evidence_term_hits,
        "cited_email_ids": output.source_email_ids,
    }


def aggregate_generation_scores(rows: Sequence[dict[str, Any]]) -> dict[str, float]:
    metric_names = (
        "groundedness",
        "answer_relevance",
        "citation_correctness",
        "refusal_correctness",
    )
    return {
        metric: sum(float(row["scores"][metric]) for row in rows) / len(rows) if rows else 0.0
        for metric in metric_names
    }
