"""Dense retrieval evaluation using HitRate@k and MRR@k."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from securemail.evaluation import RetrievalGroundTruthRecord

from .dense import DenseRetriever


def evaluate_dense_retrieval(
    retriever: DenseRetriever,
    questions: Iterable[RetrievalGroundTruthRecord],
    *,
    k: int = 5,
) -> dict[str, Any]:
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
    count = len(rows)
    return {
        "retriever": "dense",
        "k": k,
        "num_questions": count,
        "hit_rate_at_5": hit_count / count if count else 0.0,
        "mrr_at_5": reciprocal_sum / count if count else 0.0,
        "per_question": rows,
    }


def write_evaluation_results(results: dict[str, Any], path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(results, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
