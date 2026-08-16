"""Dense retrieval evaluation using HitRate@k and MRR@k."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from securemail.evaluation import RetrievalGroundTruthRecord

from .dense import DenseRetriever
from .interfaces import Retriever


def evaluate_retriever(
    retriever: Retriever,
    questions: Iterable[RetrievalGroundTruthRecord],
    *,
    name: str,
    k: int = 5,
    include_result_details: bool = False,
) -> dict[str, Any]:
    """Evaluate any interchangeable retriever with the shared retrieval contract."""

    if k <= 0:
        raise ValueError("k must be greater than zero")
    rows: list[dict[str, Any]] = []
    hit_count = 0
    reciprocal_sum = 0.0
    for item in questions:
        results = retriever.retrieve(item.question, top_k=k)
        retrieved_ids = [result.email_id for result in results]
        relevant_ids = set(item.relevant_email_ids)
        rank = next(
            (
                position
                for position, email_id in enumerate(retrieved_ids, start=1)
                if email_id in relevant_ids
            ),
            None,
        )
        if rank is not None:
            hit_count += 1
            reciprocal_sum += 1.0 / rank
        rows.append(
            {
                "id": item.id,
                "question": item.question,
                "relevant_email_ids": item.relevant_email_ids,
                "retrieved_email_ids": retrieved_ids,
                "first_relevant_rank": rank,
            }
        )
        if include_result_details:
            rows[-1]["result_details"] = [
                {
                    "email_id": result.email_id,
                    "score": getattr(
                        result,
                        "score",
                        getattr(result, "reranker_score", None),
                    ),
                    "retrieval_score": getattr(result, "retrieval_score", None),
                    "retrieval_rank": getattr(result, "retrieval_rank", None),
                    "reranker_score": getattr(result, "reranker_score", None),
                }
                for result in results
            ]
    count = len(rows)
    return {
        "retriever": name,
        "k": k,
        "num_questions": count,
        "hit_rate_at_5": hit_count / count if count else 0.0,
        "mrr_at_5": reciprocal_sum / count if count else 0.0,
        "per_question": rows,
    }


def evaluate_dense_retrieval(
    retriever: DenseRetriever,
    questions: Iterable[RetrievalGroundTruthRecord],
    *,
    k: int = 5,
) -> dict[str, Any]:
    return evaluate_retriever(retriever, questions, name="dense", k=k)


def write_evaluation_results(results: dict[str, Any], path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(results, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def compare_retrieval_results(results_by_name: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Create an auditable per-question comparison without changing ground truth."""

    required = {"dense", "bm25", "hybrid"}
    missing = required - results_by_name.keys()
    if missing:
        raise ValueError(f"comparison is missing retrievers: {sorted(missing)}")
    rows_by_name = {
        name: {row["id"]: row for row in result["per_question"]}
        for name, result in results_by_name.items()
    }
    question_ids = list(rows_by_name["dense"])
    if any(set(rows) != set(question_ids) for rows in rows_by_name.values()):
        raise ValueError("retrievers must be evaluated on the same question IDs")

    def rank(row: dict[str, Any]) -> int:
        return row["first_relevant_rank"] or 10**9

    comparisons: list[dict[str, Any]] = []
    categories = {
        "bm25_beats_dense": [],
        "dense_beats_bm25": [],
        "hybrid_improves_either": [],
        "hybrid_fails_to_improve": [],
    }
    for question_id in question_ids:
        rows = {name: rows_by_name[name][question_id] for name in required}
        ranks = {name: rank(rows[name]) for name in required}
        labels: list[str] = []
        if ranks["bm25"] < ranks["dense"]:
            labels.append("bm25_beats_dense")
            categories["bm25_beats_dense"].append(question_id)
        elif ranks["dense"] < ranks["bm25"]:
            labels.append("dense_beats_bm25")
            categories["dense_beats_bm25"].append(question_id)
        if ranks["hybrid"] < ranks["dense"] or ranks["hybrid"] < ranks["bm25"]:
            labels.append("hybrid_improves_either")
            categories["hybrid_improves_either"].append(question_id)
        else:
            labels.append("hybrid_fails_to_improve")
            categories["hybrid_fails_to_improve"].append(question_id)
        comparisons.append(
            {
                "id": question_id,
                "question": rows["dense"]["question"],
                "relevant_email_ids": rows["dense"]["relevant_email_ids"],
                "first_relevant_rank": ranks,
                "retrieved_email_ids": {
                    name: rows[name]["retrieved_email_ids"] for name in ("dense", "bm25", "hybrid")
                },
                "labels": labels,
            }
        )
    return {"categories": categories, "per_query": comparisons}
