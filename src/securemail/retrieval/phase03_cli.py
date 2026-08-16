"""Evaluate dense, BM25, and RRF hybrid retrieval on the Phase 02 corpus."""

from __future__ import annotations

import argparse
from pathlib import Path

from securemail.evaluation import RetrievalGroundTruthRecord, load_records

from .bm25 import BM25Config, BM25Retriever
from .dense import DenseRetriever
from .embeddings import SentenceTransformerEmbedder
from .evaluation import (
    compare_retrieval_results,
    evaluate_retriever,
    write_evaluation_results,
)
from .hybrid import HybridRetriever, RRFConfig
from .indexing import build_dense_index


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate Phase 03 Enron retrieval")
    parser.add_argument("--data", type=Path, default=Path("data/sample/enron_dev_500.jsonl"))
    parser.add_argument(
        "--ground-truth",
        type=Path,
        default=Path("evals/datasets/retrieval_ground_truth.phase02.json"),
    )
    parser.add_argument("--output-dir", type=Path, default=Path("evals/results"))
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--candidate-k", type=int, default=20)
    parser.add_argument("--rrf-rank-constant", type=int, default=60)
    parser.add_argument("--bm25-k1", type=float, default=1.5)
    parser.add_argument("--bm25-b", type=float, default=0.75)
    parser.add_argument("--limit", type=int, default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    embedder = SentenceTransformerEmbedder()
    index = build_dense_index(args.data, embedder, limit=args.limit)
    dense = DenseRetriever(embedder=embedder, index=index, top_k=args.top_k)
    bm25 = BM25Retriever(
        index.documents,
        top_k=args.top_k,
        config=BM25Config(k1=args.bm25_k1, b=args.bm25_b),
    )
    hybrid = HybridRetriever(
        dense,
        bm25,
        top_k=args.top_k,
        config=RRFConfig(
            rank_constant=args.rrf_rank_constant,
            candidate_k=args.candidate_k,
        ),
    )
    questions = load_records(args.ground_truth, RetrievalGroundTruthRecord)
    retrievers = {"dense": dense, "bm25": bm25, "hybrid": hybrid}
    results = {
        name: evaluate_retriever(retriever, questions, name=name, k=args.top_k)
        for name, retriever in retrievers.items()
    }
    for name, result in results.items():
        result["indexed_documents"] = len(index.documents)
        if name == "dense":
            result["embedding_model"] = embedder.model_name
        if name == "bm25":
            result["bm25_k1"] = args.bm25_k1
            result["bm25_b"] = args.bm25_b
        if name == "hybrid":
            result["rrf_rank_constant"] = args.rrf_rank_constant
            result["rrf_candidate_k"] = args.candidate_k
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_evaluation_results(results["dense"], args.output_dir / "dense_retrieval_phase03.json")
    write_evaluation_results(results["bm25"], args.output_dir / "bm25_retrieval_phase03.json")
    write_evaluation_results(results["hybrid"], args.output_dir / "hybrid_retrieval_phase03.json")
    comparison = compare_retrieval_results(results)
    comparison["corpus_size"] = len(index.documents)
    comparison["question_count"] = len(questions)
    comparison["k"] = args.top_k
    comparison["rrf_rank_constant"] = args.rrf_rank_constant
    comparison["rrf_candidate_k"] = args.candidate_k
    comparison["bm25_k1"] = args.bm25_k1
    comparison["bm25_b"] = args.bm25_b
    comparison["metrics"] = {
        name: {
            "hit_rate_at_5": result["hit_rate_at_5"],
            "mrr_at_5": result["mrr_at_5"],
        }
        for name, result in results.items()
    }
    write_evaluation_results(comparison, args.output_dir / "phase03_retrieval_comparison.json")
    for name, result in results.items():
        print(
            f"{name} HitRate@{args.top_k}={result['hit_rate_at_5']:.4f} "
            f"MRR@{args.top_k}={result['mrr_at_5']:.4f} "
            f"questions={result['num_questions']} documents={len(index.documents)}"
        )


if __name__ == "__main__":
    main()
