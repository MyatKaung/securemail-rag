"""Evaluate optional query rewriting against the unchanged Phase 04 baseline."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from securemail.evaluation import RetrievalGroundTruthRecord, load_records

from .bm25 import BM25Config, BM25Retriever
from .dense import DenseRetriever
from .embeddings import SentenceTransformerEmbedder
from .evaluation import evaluate_retriever, write_evaluation_results
from .hybrid import HybridRetriever, RRFConfig
from .index import DenseIndex
from .indexing import build_dense_index
from .query_rewriting import (
    CachedQueryRewriter,
    OpenRouterQueryRewriter,
    QueryRewriteConfig,
    RewritingRetriever,
)
from .reranking import CrossEncoderReranker, RerankedRetriever


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate optional Phase 10 query rewriting")
    parser.add_argument("--data", type=Path, default=Path("data/sample/enron_dev_500.jsonl"))
    parser.add_argument(
        "--ground-truth",
        type=Path,
        default=Path("evals/datasets/retrieval_ground_truth.phase02.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("evals/results/phase10_query_rewriting.json"),
    )
    parser.add_argument("--candidate-k", type=int, default=20)
    parser.add_argument("--final-k", type=int, default=5)
    parser.add_argument("--rrf-rank-constant", type=int, default=60)
    parser.add_argument("--bm25-k1", type=float, default=1.5)
    parser.add_argument("--bm25-b", type=float, default=0.75)
    parser.add_argument("--reranker-model", type=str, default=None)
    parser.add_argument(
        "--live-rewrite",
        action="store_true",
        help="allow cached misses to call OpenRouter; without this flag, cache must be complete",
    )
    parser.add_argument(
        "--enable-query-rewrite",
        action="store_true",
        help="enable the treatment retriever; the default production path remains unchanged",
    )
    return parser


def _rank(row: dict[str, Any]) -> int:
    return row["first_relevant_rank"] or 10**9


def evaluate_rewritten(
    retriever: RewritingRetriever,
    questions: list[RetrievalGroundTruthRecord],
    *,
    k: int,
) -> dict[str, Any]:
    """Evaluate while recording the exact query sent to the baseline retriever."""

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
                "original_query": retriever.last_original_query,
                "rewritten_query": retriever.last_rewritten_query,
                "rewrite_fallback_used": retriever.last_fallback_used,
                "retrieved_email_ids": retrieved_ids,
                "first_relevant_rank": rank,
            }
        )
    count = len(rows)
    return {
        "retriever": "query_rewrite_hybrid_reranked",
        "k": k,
        "num_questions": count,
        "hit_rate_at_5": hit_count / count if count else 0.0,
        "mrr_at_5": reciprocal_sum / count if count else 0.0,
        "per_question": rows,
    }


def compare_results(
    baseline: dict[str, Any], treatment: dict[str, Any]
) -> tuple[dict[str, list[str]], list[dict[str, Any]]]:
    baseline_rows = {row["id"]: row for row in baseline["per_question"]}
    treatment_rows = {row["id"]: row for row in treatment["per_question"]}
    if set(baseline_rows) != set(treatment_rows):
        raise ValueError("baseline and rewrite evaluations must cover the same questions")

    categories = {"improved": [], "unchanged": [], "worse": []}
    rows: list[dict[str, Any]] = []
    for question_id, original in baseline_rows.items():
        rewritten = treatment_rows[question_id]
        original_rank = _rank(original)
        rewritten_rank = _rank(rewritten)
        if rewritten_rank < original_rank:
            category = "improved"
        elif rewritten_rank == original_rank:
            category = "unchanged"
        else:
            category = "worse"
        categories[category].append(question_id)
        rows.append(
            {
                "id": question_id,
                "question": original["question"],
                "relevant_email_ids": original["relevant_email_ids"],
                "original_query": treatment_rows[question_id]["original_query"],
                "rewritten_query": treatment_rows[question_id]["rewritten_query"],
                "baseline_first_relevant_rank": original["first_relevant_rank"],
                "rewritten_first_relevant_rank": rewritten["first_relevant_rank"],
                "rank_change": (
                    None
                    if 10**9 in {original_rank, rewritten_rank}
                    else original_rank - rewritten_rank
                ),
                "baseline_retrieved_email_ids": original["retrieved_email_ids"],
                "rewritten_retrieved_email_ids": rewritten["retrieved_email_ids"],
                "rewrite_fallback_used": rewritten["rewrite_fallback_used"],
                "category": category,
            }
        )
    return categories, rows


def _build_reranked(
    index: DenseIndex,
    embedder: SentenceTransformerEmbedder,
    *,
    candidate_k: int,
    final_k: int,
    rrf_rank_constant: int,
    bm25_k1: float,
    bm25_b: float,
    reranker_model: str | None,
) -> RerankedRetriever:
    dense = DenseRetriever(embedder=embedder, index=index, top_k=candidate_k)
    bm25 = BM25Retriever(
        index.documents,
        top_k=candidate_k,
        config=BM25Config(k1=bm25_k1, b=bm25_b),
    )
    hybrid = HybridRetriever(
        dense,
        bm25,
        top_k=final_k,
        config=RRFConfig(rank_constant=rrf_rank_constant, candidate_k=candidate_k),
    )
    return RerankedRetriever(
        hybrid,
        CrossEncoderReranker(model_name=reranker_model),
        candidate_k=candidate_k,
        final_k=final_k,
    )


def main() -> None:
    args = build_parser().parse_args()
    config = QueryRewriteConfig(
        enabled=args.enable_query_rewrite or QueryRewriteConfig.from_environment().enabled
    )
    if not config.enabled:
        raise SystemExit("query rewriting is disabled; pass --enable-query-rewrite or set ENABLE_QUERY_REWRITE=true")

    questions = load_records(args.ground_truth, RetrievalGroundTruthRecord)
    embedder = SentenceTransformerEmbedder()
    index = build_dense_index(args.data, embedder)
    baseline_reranked = _build_reranked(
        index,
        embedder,
        candidate_k=args.candidate_k,
        final_k=args.final_k,
        rrf_rank_constant=args.rrf_rank_constant,
        bm25_k1=args.bm25_k1,
        bm25_b=args.bm25_b,
        reranker_model=args.reranker_model,
    )
    baseline_results = evaluate_retriever(
        baseline_reranked,
        questions,
        name="hybrid_reranked_original",
        k=args.final_k,
    )

    rewrite_client = OpenRouterQueryRewriter() if args.live_rewrite else None
    cached_rewriter = CachedQueryRewriter(rewrite_client, cache_path=args.output)
    missing = [item.question for item in questions if item.question not in cached_rewriter.cached_queries]
    if missing and not args.live_rewrite:
        raise SystemExit(
            f"rewrite cache is missing {len(missing)} question(s); rerun with --live-rewrite"
        )

    treatment_reranked = _build_reranked(
        index,
        embedder,
        candidate_k=args.candidate_k,
        final_k=args.final_k,
        rrf_rank_constant=args.rrf_rank_constant,
        bm25_k1=args.bm25_k1,
        bm25_b=args.bm25_b,
        reranker_model=args.reranker_model,
    )
    treatment = RewritingRetriever(
        treatment_reranked,
        cached_rewriter,
        config=QueryRewriteConfig(enabled=True),
    )
    rewrite_results = evaluate_rewritten(treatment, questions, k=args.final_k)
    categories, per_query = compare_results(baseline_results, rewrite_results)
    examples = {
        category: next((row for row in per_query if row["category"] == category), None)
        for category in categories
    }
    index_size = len(baseline_reranked.candidate_retriever.dense.index.documents)
    result = {
        "phase": 10,
        "experiment": "query_rewriting",
        "prompt_version": "query_rewrite_v1",
        "rewrite_model": rewrite_client.client.settings.model if rewrite_client else "cached",
        "corpus_size": index_size,
        "question_count": len(questions),
        "candidate_k": args.candidate_k,
        "final_k": args.final_k,
        "rrf_rank_constant": args.rrf_rank_constant,
        "reranker_model": treatment_reranked.reranker.model_name,
        "feature_flag_enabled": config.enabled,
        "live_rewrite_requested": args.live_rewrite,
        "openrouter_rewrite_calls": rewrite_client.call_count if rewrite_client else 0,
        "rewrite_cache_hits": cached_rewriter.cache_hits,
        "rewrite_cache_misses": cached_rewriter.cache_misses,
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "metrics": {
            "baseline_hybrid_reranked": {
                "hit_rate_at_5": baseline_results["hit_rate_at_5"],
                "mrr_at_5": baseline_results["mrr_at_5"],
            },
            "query_rewrite_hybrid_reranked": {
                "hit_rate_at_5": rewrite_results["hit_rate_at_5"],
                "mrr_at_5": rewrite_results["mrr_at_5"],
            },
        },
        "categories": categories,
        "examples": examples,
        "rewrites": {
            row["original_query"]: {
                "rewritten_query": row["rewritten_query"],
                "fallback_used": row["rewrite_fallback_used"],
            }
            for row in per_query
        },
        "per_query": per_query,
    }
    write_evaluation_results(result, args.output)
    print(
        f"baseline HitRate@{args.final_k}={baseline_results['hit_rate_at_5']:.4f} "
        f"MRR@{args.final_k}={baseline_results['mrr_at_5']:.4f}"
    )
    print(
        f"rewritten HitRate@{args.final_k}={rewrite_results['hit_rate_at_5']:.4f} "
        f"MRR@{args.final_k}={rewrite_results['mrr_at_5']:.4f}"
    )
    print(f"openrouter_rewrite_calls={result['openrouter_rewrite_calls']}")
    print(f"categories={categories}")


if __name__ == "__main__":
    main()
