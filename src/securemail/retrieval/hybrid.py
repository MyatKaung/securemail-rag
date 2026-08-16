"""Hybrid BM25+dense retrieval using Reciprocal Rank Fusion."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .index import DenseSearchResult
from .interfaces import Retriever

if TYPE_CHECKING:
    from securemail.security.authorization import AuthorizationFilter


@dataclass(frozen=True)
class RRFConfig:
    """Explicit RRF settings; ranks are one-based in the formula."""

    rank_constant: int = 60
    candidate_k: int = 20

    def __post_init__(self) -> None:
        if self.rank_constant <= 0:
            raise ValueError("rank_constant must be greater than zero")
        if self.candidate_k <= 0:
            raise ValueError("candidate_k must be greater than zero")


def rrf_fuse(
    rankings: Sequence[Sequence[DenseSearchResult]],
    *,
    config: RRFConfig | None = None,
    top_k: int = 5,
) -> list[DenseSearchResult]:
    """Fuse ranked lists with ``score(d)=sum(1/(c+rank(d)))``."""

    if top_k <= 0:
        raise ValueError("top_k must be greater than zero")
    fusion_config = config or RRFConfig()
    fused_scores: dict[str, float] = {}
    representatives: dict[str, DenseSearchResult] = {}
    first_seen: dict[str, int] = {}
    seen_counter = 0
    for ranking in rankings:
        for rank, result in enumerate(ranking, start=1):
            email_id = result.email_id
            fused_scores[email_id] = fused_scores.get(email_id, 0.0) + 1.0 / (
                fusion_config.rank_constant + rank
            )
            representatives.setdefault(email_id, result)
            first_seen.setdefault(email_id, seen_counter)
            seen_counter += 1
    ordered_ids = sorted(
        fused_scores,
        key=lambda email_id: (-fused_scores[email_id], first_seen[email_id], email_id),
    )
    return [
        DenseSearchResult(
            email_id=email_id,
            score=fused_scores[email_id],
            document=representatives[email_id].document,
        )
        for email_id in ordered_ids[:top_k]
    ]


class HybridRetriever:
    """Run dense and BM25 retrieval independently, then fuse their rankings."""

    def __init__(
        self,
        dense: Retriever,
        bm25: Retriever,
        *,
        top_k: int = 5,
        config: RRFConfig | None = None,
        authorization_filter: AuthorizationFilter | None = None,
    ) -> None:
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")
        self.dense = dense
        self.bm25 = bm25
        self.top_k = top_k
        self.config = config or RRFConfig()
        self.authorization_filter = authorization_filter
        if authorization_filter is not None:
            self.set_authorization_filter(authorization_filter)

    def set_authorization_filter(self, authorization_filter: AuthorizationFilter) -> None:
        for retriever in (self.dense, self.bm25):
            setter = getattr(retriever, "set_authorization_filter", None)
            if setter is None:
                raise TypeError("all hybrid retrievers must support pre-retrieval authorization")
            setter(authorization_filter)
        self.authorization_filter = authorization_filter

    def retrieve(self, question: str, top_k: int | None = None) -> list[DenseSearchResult]:
        requested_k = self.top_k if top_k is None else top_k
        if requested_k <= 0:
            raise ValueError("top_k must be greater than zero")
        candidate_k = max(requested_k, self.config.candidate_k)
        dense_results = self.dense.retrieve(question, top_k=candidate_k)
        bm25_results = self.bm25.retrieve(question, top_k=candidate_k)
        return rrf_fuse(
            (dense_results, bm25_results),
            config=self.config,
            top_k=requested_k,
        )
