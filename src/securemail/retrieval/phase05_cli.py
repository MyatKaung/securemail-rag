"""Evaluate pre-retrieval authorization against an intentionally insecure baseline."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from securemail.evaluation import PermissionTestRecord, load_records
from securemail.ingestion.rbac import SYNTHETIC_POLICY_VERSION
from securemail.security import AuthorizationFilter, PrincipalContext, SyntheticRBACPolicy

from .bm25 import BM25Config, BM25Retriever
from .dense import DenseRetriever
from .embeddings import SentenceTransformerEmbedder
from .evaluation import write_evaluation_results
from .hybrid import HybridRetriever, RRFConfig
from .indexing import build_dense_index
from .reranking import CrossEncoderReranker, RerankedRetriever


def _build_permission_retriever(
    index: Any,
    embedder: SentenceTransformerEmbedder,
    reranker: CrossEncoderReranker,
    *,
    candidate_k: int,
    final_k: int,
    principal: PrincipalContext | None,
) -> RerankedRetriever:
    authorization_filter = (
        AuthorizationFilter(principal, SyntheticRBACPolicy()) if principal is not None else None
    )
    dense = DenseRetriever(
        embedder=embedder,
        index=index,
        top_k=candidate_k,
        authorization_filter=authorization_filter,
    )
    bm25 = BM25Retriever(
        index.documents,
        top_k=candidate_k,
        config=BM25Config(),
        authorization_filter=authorization_filter,
    )
    hybrid = HybridRetriever(
        dense,
        bm25,
        top_k=final_k,
        config=RRFConfig(candidate_k=candidate_k),
        authorization_filter=authorization_filter,
    )
    return RerankedRetriever(
        hybrid,
        reranker,
        candidate_k=candidate_k,
        final_k=final_k,
        authorization_filter=authorization_filter,
    )


def _first_relevant_rank(retrieved_ids: list[str], relevant_ids: list[str]) -> int | None:
    relevant = set(relevant_ids)
    return next(
        (rank for rank, email_id in enumerate(retrieved_ids, start=1) if email_id in relevant),
        None,
    )


def evaluate_permission_cases(
    cases: list[PermissionTestRecord],
    *,
    no_filter_retriever: RerankedRetriever,
    filtered_retriever_factory: Any,
    documents_by_id: dict[str, Any],
    policy: SyntheticRBACPolicy,
    k: int,
) -> dict[str, Any]:
    denial_cases = [case for case in cases if case.expected == "deny"]
    no_filter_unauthorized = 0
    filtered_unauthorized = 0
    decision_checks = 0
    correct_decisions = 0
    authorized_hits = 0
    authorized_reciprocal_sum = 0.0
    allowed_case_count = 0
    per_case: list[dict[str, Any]] = []

    for case in cases:
        principal = PrincipalContext(**case.principal.model_dump())
        no_filter_results = no_filter_retriever.retrieve(case.question, top_k=k)
        filtered_retriever = filtered_retriever_factory(principal)
        filtered_results = filtered_retriever.retrieve(case.question, top_k=k)
        no_filter_ids = [result.email_id for result in no_filter_results]
        filtered_ids = [result.email_id for result in filtered_results]
        no_filter_leak = bool(set(no_filter_ids) & set(case.forbidden_email_ids))
        filtered_leak = bool(set(filtered_ids) & set(case.forbidden_email_ids))
        if case.expected == "deny":
            no_filter_unauthorized += no_filter_leak
            filtered_unauthorized += filtered_leak

        policy_checks: list[dict[str, Any]] = []
        for email_id in case.allowed_email_ids:
            actual = policy.is_allowed(principal, documents_by_id[email_id].metadata)
            decision_checks += 1
            correct_decisions += actual
            policy_checks.append({"email_id": email_id, "expected": True, "actual": actual})
        for email_id in case.forbidden_email_ids:
            actual = policy.is_allowed(principal, documents_by_id[email_id].metadata)
            decision_checks += 1
            correct_decisions += not actual
            policy_checks.append({"email_id": email_id, "expected": False, "actual": actual})

        filtered_rank = _first_relevant_rank(filtered_ids, case.allowed_email_ids)
        if case.expected == "allow":
            allowed_case_count += 1
            if filtered_rank is not None:
                authorized_hits += 1
                authorized_reciprocal_sum += 1.0 / filtered_rank
        per_case.append(
            {
                "id": case.id,
                "case_type": case.case_type,
                "question": case.question,
                "expected": case.expected,
                "principal": case.principal.model_dump(),
                "allowed_email_ids": case.allowed_email_ids,
                "forbidden_email_ids": case.forbidden_email_ids,
                "no_filter_retrieved_email_ids": no_filter_ids,
                "filtered_retrieved_email_ids": filtered_ids,
                "no_filter_unauthorized": no_filter_leak,
                "filtered_unauthorized": filtered_leak,
                "filtered_first_authorized_rank": filtered_rank,
                "policy_checks": policy_checks,
            }
        )

    return {
        "num_cases": len(cases),
        "num_denial_cases": len(denial_cases),
        "no_filter_unauthorized_retrieval_rate": (
            no_filter_unauthorized / len(denial_cases) if denial_cases else 0.0
        ),
        "filtered_unauthorized_retrieval_rate": (
            filtered_unauthorized / len(denial_cases) if denial_cases else 0.0
        ),
        "authorization_decision_accuracy": (
            correct_decisions / decision_checks if decision_checks else 0.0
        ),
        "authorized_case_count": allowed_case_count,
        "authorized_hit_rate_at_5": (
            authorized_hits / allowed_case_count if allowed_case_count else 0.0
        ),
        "authorized_mrr_at_5": (
            authorized_reciprocal_sum / allowed_case_count if allowed_case_count else 0.0
        ),
        "per_case": per_case,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate Phase 05 permission-aware retrieval")
    parser.add_argument("--data", type=Path, default=Path("data/sample/enron_dev_500.jsonl"))
    parser.add_argument(
        "--permissions",
        type=Path,
        default=Path("evals/datasets/permission_ground_truth.phase05.json"),
    )
    parser.add_argument(
        "--output", type=Path, default=Path("evals/results/phase05_permission.json")
    )
    parser.add_argument("--candidate-k", type=int, default=20)
    parser.add_argument("--final-k", type=int, default=5)
    parser.add_argument("--limit", type=int, default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    embedder = SentenceTransformerEmbedder()
    index = build_dense_index(args.data, embedder, limit=args.limit)
    documents_by_id = {document.email_id: document for document in index.documents}
    cases = load_records(args.permissions, PermissionTestRecord)
    policy = SyntheticRBACPolicy()
    reranker = CrossEncoderReranker()
    no_filter_retriever = _build_permission_retriever(
        index,
        embedder,
        reranker,
        candidate_k=args.candidate_k,
        final_k=args.final_k,
        principal=None,
    )

    def filtered_retriever_factory(principal: PrincipalContext) -> RerankedRetriever:
        return _build_permission_retriever(
            index,
            embedder,
            reranker,
            candidate_k=args.candidate_k,
            final_k=args.final_k,
            principal=principal,
        )

    results = evaluate_permission_cases(
        cases,
        no_filter_retriever=no_filter_retriever,
        filtered_retriever_factory=filtered_retriever_factory,
        documents_by_id=documents_by_id,
        policy=policy,
        k=args.final_k,
    )
    results.update(
        {
            "corpus_size": len(index.documents),
            "candidate_k": args.candidate_k,
            "final_k": args.final_k,
            "policy": "SyntheticRBACPolicy",
            "policy_version": SYNTHETIC_POLICY_VERSION,
            "retriever": "hybrid_plus_reranker",
            "reranker_model": reranker.model_name,
        }
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_evaluation_results(results, args.output)
    print(
        f"no_filter_URR={results['no_filter_unauthorized_retrieval_rate']:.4f} "
        f"filtered_URR={results['filtered_unauthorized_retrieval_rate']:.4f} "
        f"decision_accuracy={results['authorization_decision_accuracy']:.4f} "
        f"authorized_HitRate@5={results['authorized_hit_rate_at_5']:.4f} "
        f"authorized_MRR@5={results['authorized_mrr_at_5']:.4f} "
        f"cases={results['num_cases']} documents={results['corpus_size']}"
    )


if __name__ == "__main__":
    main()
