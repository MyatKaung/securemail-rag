"""Opt-in live Qwen smoke test; never run this from the default test suite."""

from __future__ import annotations

import argparse
from pathlib import Path

from securemail.generation import (
    STRUCTURED_GROUNDED_STRATEGY,
    OpenRouterGenerationClient,
    PermissionAwareGenerationPipeline,
)
from securemail.retrieval.documents import prepare_document
from securemail.retrieval.index import DenseSearchResult
from securemail.retrieval.indexing import load_normalized_jsonl
from securemail.security import AuthorizationFilter, PrincipalContext, SyntheticRBACPolicy


class StaticRetriever:
    def __init__(self, result: DenseSearchResult) -> None:
        self.result = result

    def set_authorization_filter(self, authorization_filter: AuthorizationFilter) -> None:
        self.authorization_filter = authorization_filter

    def retrieve(self, question: str, top_k: int | None = None) -> list[DenseSearchResult]:
        del question, top_k
        return [self.result]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Opt-in live Qwen/OpenRouter smoke test")
    parser.add_argument("--data", type=Path, default=Path("data/sample/enron_dev_500.jsonl"))
    parser.add_argument("--question", default="What is the subject of the supplied email?")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    email = load_normalized_jsonl(args.data, limit=1)[0]
    document = prepare_document(email)
    principal = PrincipalContext("admin", "global", "global", "global")
    authorization_filter = AuthorizationFilter(principal, SyntheticRBACPolicy())
    retriever = StaticRetriever(DenseSearchResult(document.email_id, 1.0, document))
    pipeline = PermissionAwareGenerationPipeline(
        retriever,
        OpenRouterGenerationClient(),
        authorization_filter,
        STRUCTURED_GROUNDED_STRATEGY,
    )
    result = pipeline.answer(args.question, top_k=1)
    print(result.answer)
    print(f"sources={result.source_email_ids}")


if __name__ == "__main__":
    main()
