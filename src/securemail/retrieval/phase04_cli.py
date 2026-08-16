"""Evaluate Phase 04 hybrid retrieval with cross-encoder reranking."""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Any

from securemail.evaluation import RetrievalGroundTruthRecord, load_records

from .bm25 import BM25Config, BM25Retriever
from .dense import DenseRetriever
from .embeddings import SentenceTransformerEmbedder
from .evaluation import evaluate_retriever, write_evaluation_results
from .hybrid import HybridRetriever, RRFConfig
from .indexing import build_dense_index
from .reranking import CrossEncoderReranker, RerankedRetriever


def compare_reranking_results(
    hybrid_results: dict[str, Any], reranked_results: dict[str, Any]
) -> dict[str, Any]:
    """Record whether reranking improves, preserves, or worsens relevant rank."""

    hybrid_rows = {row["id"]: row for row in hybrid_results["per_question"]}
    reranked_rows = {row["id"]: row for row in reranked_results["per_question"]}
    if set(hybrid_rows) != set(reranked_rows):
        raise ValueError("hybrid and reranked results must cover the same questions")

    def rank(row: dict[str, Any]) -> int:
        return row["first_relevant_rank"] or 10**9

    categories = {"improved": [], "unchanged": [], "worse": []}
    per_query = []
    for question_id, hybrid_row in hybrid_rows.items():
        reranked_row = reranked_rows[question_id]
        hybrid_rank = rank(hybrid_row)
        reranked_rank = rank(reranked_row)
        if reranked_rank < hybrid_rank:
            label = "improved"
        elif reranked_rank == hybrid_rank:
            label = "unchanged"
        else:
            label = "worse"
        categories[label].append(question_id)
        per_query.append(
            {
                "id": question_id,
                "question": hybrid_row["question"],
                "relevant_email_ids": hybrid_row["relevant_email_ids"],
                "hybrid_first_relevant_rank": hybrid_row["first_relevant_rank"],
                "reranked_first_relevant_rank": reranked_row["first_relevant_rank"],
                "rank_change": (
                    None if 10**9 in {hybrid_rank, reranked_rank} else hybrid_rank - reranked_rank
                ),
                "hybrid_retrieved_email_ids": hybrid_row["retrieved_email_ids"],
                "reranked_retrieved_email_ids": reranked_row["retrieved_email_ids"],
                "reranked_result_details": reranked_row.get("result_details", []),
                "category": label,
            }
        )
    return {"categories": categories, "per_query": per_query}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate Phase 04 reranking")
    parser.add_argument("--data", type=Path, default=Path("data/sample/enron_dev_500.jsonl"))
    parser.add_argument(
        "--ground-truth",
        type=Path,
        default=Path("evals/datasets/retrieval_ground_truth.phase02.json"),
    )
    parser.add_argument("--output-dir", type=Path, default=Path("evals/results"))
    parser.add_argument("--candidate-k", type=int, default=20)
    parser.add_argument("--final-k", type=int, default=5)
    parser.add_argument("--rrf-rank-constant", type=int, default=60)
    parser.add_argument("--bm25-k1", type=float, default=1.5)
    parser.add_argument("--bm25-b", type=float, default=0.75)
    parser.add_argument("--reranker-model", type=str, default=None)
    parser.add_argument("--limit", type=int, default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    embedder = SentenceTransformerEmbedder()
    index = build_dense_index(args.data, embedder, limit=args.limit)
    dense = DenseRetriever(embedder=embedder, index=index, top_k=args.candidate_k)
    bm25 = BM25Retriever(
        index.documents,
        top_k=args.candidate_k,
        config=BM25Config(k1=args.bm25_k1, b=args.bm25_b),
    )
    hybrid = HybridRetriever(
        dense,
        bm25,
        top_k=args.final_k,
        config=RRFConfig(
            rank_constant=args.rrf_rank_constant,
            candidate_k=args.candidate_k,
        ),
    )
    reranker = CrossEncoderReranker(model_name=args.reranker_model)
    reranked = RerankedRetriever(
        hybrid,
        reranker,
        candidate_k=args.candidate_k,
        final_k=args.final_k,
    )
    questions = load_records(args.ground_truth, RetrievalGroundTruthRecord)
    hybrid_results = evaluate_retriever(hybrid, questions, name="hybrid", k=args.final_k)
    start = time.perf_counter()
    reranked_results = evaluate_retriever(
        reranked,
        questions,
        name="hybrid_reranked",
        k=args.final_k,
        include_result_details=True,
    )
    reranking_seconds = time.perf_counter() - start
    for result in (hybrid_results, reranked_results):
        result["indexed_documents"] = len(index.documents)
        result["candidate_k"] = args.candidate_k
        result["final_k"] = args.final_k
    hybrid_results["rrf_rank_constant"] = args.rrf_rank_constant
    reranked_results["reranker_model"] = reranker.model_name
    reranked_results["reranking_seconds"] = reranking_seconds
    reranked_results["reranking_ms_per_question"] = (
        reranking_seconds / len(questions) * 1000 if questions else 0.0
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_evaluation_results(hybrid_results, args.output_dir / "hybrid_retrieval_phase04.json")
    write_evaluation_results(
        reranked_results,
        args.output_dir / "hybrid_reranked_phase04.json",
    )
    comparison = compare_reranking_results(hybrid_results, reranked_results)
    comparison.update(
        {
            "corpus_size": len(index.documents),
            "question_count": len(questions),
            "candidate_k": args.candidate_k,
            "final_k": args.final_k,
            "reranker_model": reranker.model_name,
            "rrf_rank_constant": args.rrf_rank_constant,
            "reranking_seconds": reranking_seconds,
            "reranking_ms_per_question": reranked_results["reranking_ms_per_question"],
            "metrics": {
                "hybrid": {
                    "hit_rate_at_5": hybrid_results["hit_rate_at_5"],
                    "mrr_at_5": hybrid_results["mrr_at_5"],
                },
                "hybrid_reranked": {
                    "hit_rate_at_5": reranked_results["hit_rate_at_5"],
                    "mrr_at_5": reranked_results["mrr_at_5"],
                },
            },
        }
    )
    write_evaluation_results(
        comparison,
        args.output_dir / "phase04_reranking_comparison.json",
    )
    for result in (hybrid_results, reranked_results):
        print(
            f"{result['retriever']} HitRate@{args.final_k}={result['hit_rate_at_5']:.4f} "
            f"MRR@{args.final_k}={result['mrr_at_5']:.4f} "
            f"questions={result['num_questions']} documents={len(index.documents)}"
        )
    print(f"reranking_ms_per_question={reranked_results['reranking_ms_per_question']:.2f}")


if __name__ == "__main__":
    main()
