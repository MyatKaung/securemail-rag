"""Run the live Phase 06 grounded-generation evaluation."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from securemail.evaluation import GenerationEvaluationRecord, load_records
from securemail.generation import (
    BASIC_GROUNDED_V1,
    STRUCTURED_GROUNDED_V1,
    OpenRouterGenerationClient,
    PermissionAwareGenerationPipeline,
    get_prompt_strategy,
)
from securemail.generation.evaluation import aggregate_generation_scores, score_generation_output
from securemail.retrieval.bm25 import BM25Config, BM25Retriever
from securemail.retrieval.dense import DenseRetriever
from securemail.retrieval.embeddings import SentenceTransformerEmbedder
from securemail.retrieval.evaluation import write_evaluation_results
from securemail.retrieval.hybrid import HybridRetriever, RRFConfig
from securemail.retrieval.indexing import build_dense_index
from securemail.retrieval.reranking import CrossEncoderReranker, RerankedRetriever
from securemail.security import AuthorizationFilter, PrincipalContext, SyntheticRBACPolicy


def _build_pipeline(
    index: Any,
    embedder: SentenceTransformerEmbedder,
    reranker: CrossEncoderReranker,
    generator: OpenRouterGenerationClient,
    case: GenerationEvaluationRecord,
    strategy_name: str,
    *,
    candidate_k: int,
    final_k: int,
) -> PermissionAwareGenerationPipeline:
    principal = PrincipalContext(**case.principal.model_dump())
    authorization_filter = AuthorizationFilter(principal, SyntheticRBACPolicy())
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
    reranked = RerankedRetriever(
        hybrid,
        reranker,
        candidate_k=candidate_k,
        final_k=final_k,
        authorization_filter=authorization_filter,
    )
    return PermissionAwareGenerationPipeline(
        reranked,
        generator,
        authorization_filter,
        get_prompt_strategy(strategy_name),
    )


def _evaluate_strategy(
    cases: list[GenerationEvaluationRecord],
    *,
    strategy_name: str,
    index: Any,
    embedder: SentenceTransformerEmbedder,
    reranker: CrossEncoderReranker,
    generator: OpenRouterGenerationClient,
    candidate_k: int,
    final_k: int,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for case in cases:
        pipeline = _build_pipeline(
            index,
            embedder,
            reranker,
            generator,
            case,
            strategy_name,
            candidate_k=candidate_k,
            final_k=final_k,
        )
        result = pipeline.answer(case.question, top_k=final_k)
        evidence_ids = [item.email_id for item in result.retrieved]
        evidence_text = "\n".join(item.document.text for item in result.retrieved)
        scores = score_generation_output(
            case,
            result.parsed,
            authorized_source_ids=evidence_ids,
            evidence_text=evidence_text,
        )
        rows.append(
            {
                "id": case.id,
                "case_type": case.case_type,
                "question": case.question,
                "principal": case.principal.model_dump(),
                "retrieved_email_ids": evidence_ids,
                "answer": result.answer,
                "source_email_ids": result.source_email_ids,
                "uncertainty": result.parsed.uncertainty,
                "refused": result.parsed.refused,
                "prompt_version": result.prompt_version,
                "scores": scores,
            }
        )
    return {
        "strategy": strategy_name,
        "prompt_version": get_prompt_strategy(strategy_name).version,
        "metrics": aggregate_generation_scores(rows),
        "per_question": rows,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Phase 06 OpenRouter evaluation")
    parser.add_argument("--data", type=Path, default=Path("data/sample/enron_dev_500.jsonl"))
    parser.add_argument(
        "--ground-truth",
        type=Path,
        default=Path("evals/datasets/generation_ground_truth.phase06.json"),
    )
    parser.add_argument(
        "--output", type=Path, default=Path("evals/results/phase06_generation.json")
    )
    parser.add_argument("--candidate-k", type=int, default=20)
    parser.add_argument("--final-k", type=int, default=5)
    parser.add_argument("--limit", type=int, default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    cases = load_records(args.ground_truth, GenerationEvaluationRecord)
    embedder = SentenceTransformerEmbedder()
    index = build_dense_index(args.data, embedder, limit=args.limit)
    reranker = CrossEncoderReranker()
    generator = OpenRouterGenerationClient()
    approaches = {
        "basic_grounded": BASIC_GROUNDED_V1,
        "structured_grounded": STRUCTURED_GROUNDED_V1,
    }
    evaluated = {
        label: _evaluate_strategy(
            cases,
            strategy_name=strategy_name,
            index=index,
            embedder=embedder,
            reranker=reranker,
            generator=generator,
            candidate_k=args.candidate_k,
            final_k=args.final_k,
        )
        for label, strategy_name in approaches.items()
    }
    overall_scores = {
        label: sum(result["metrics"].values()) / len(result["metrics"])
        for label, result in evaluated.items()
    }
    selected = max(overall_scores, key=overall_scores.get)
    refusal_cases = sum(
        not case.sufficient_evidence and case.must_refuse_if_insufficient for case in cases
    )
    result = {
        "phase": 6,
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "model": generator.settings.model,
        "base_url": generator.settings.base_url,
        "corpus_size": len(index.documents),
        "question_count": len(cases),
        "candidate_k": args.candidate_k,
        "final_k": args.final_k,
        "evaluation_configuration": {
            "retrieval": "permission-aware hybrid + cross-encoder reranker",
            "judge": "deterministic term/citation/refusal rubric; no LLM judge",
            "approaches": list(approaches),
            "openrouter_calls": len(cases) * len(approaches),
        },
        "insufficient_or_refusal_case_count": refusal_cases,
        "selected_default_strategy": selected,
        "overall_scores": overall_scores,
        "approaches": evaluated,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_evaluation_results(result, args.output)
    for label, evaluation in evaluated.items():
        metrics = evaluation["metrics"]
        refusal_rows = [
            row for row in evaluation["per_question"] if row["scores"]["expected_refusal"]
        ]
        refusal_success = sum(row["scores"]["refusal_correctness"] for row in refusal_rows)
        print(
            f"{label}: groundedness={metrics['groundedness']:.4f} "
            f"relevance={metrics['answer_relevance']:.4f} "
            f"citations={metrics['citation_correctness']:.4f} "
            f"refusal={metrics['refusal_correctness']:.4f} "
            f"refusal_cases={len(refusal_rows)} "
            f"refusal_success={refusal_success / len(refusal_rows) if refusal_rows else 0:.4f}"
        )
    print(f"selected_default={selected} openrouter_calls={len(cases) * len(approaches)}")


if __name__ == "__main__":
    main()
