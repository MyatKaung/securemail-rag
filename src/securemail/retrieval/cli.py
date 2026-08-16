"""CLI for building and evaluating the Phase 02 dense baseline."""

from __future__ import annotations

import argparse
from pathlib import Path

from securemail.evaluation import RetrievalGroundTruthRecord, load_records

from .dense import DenseRetriever
from .embeddings import SentenceTransformerEmbedder
from .evaluation import evaluate_dense_retrieval, write_evaluation_results
from .indexing import build_dense_index


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate dense Enron retrieval")
    parser.add_argument("--data", type=Path, default=Path("data/sample/enron_dev_500.jsonl"))
    parser.add_argument(
        "--ground-truth",
        type=Path,
        default=Path("evals/datasets/retrieval_ground_truth.phase02.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("evals/results/dense_retrieval_phase02.json"),
    )
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--limit", type=int, default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    embedder = SentenceTransformerEmbedder()
    index = build_dense_index(args.data, embedder, limit=args.limit)
    retriever = DenseRetriever(embedder=embedder, index=index, top_k=args.top_k)
    questions = load_records(args.ground_truth, RetrievalGroundTruthRecord)
    results = evaluate_dense_retrieval(retriever, questions, k=args.top_k)
    results["embedding_model"] = embedder.model_name
    results["indexed_documents"] = len(index.documents)
    write_evaluation_results(results, args.output)
    print(
        f"dense HitRate@{args.top_k}={results['hit_rate_at_5']:.4f} "
        f"MRR@{args.top_k}={results['mrr_at_5']:.4f} "
        f"questions={results['num_questions']} documents={len(index.documents)}"
    )


if __name__ == "__main__":
    main()
