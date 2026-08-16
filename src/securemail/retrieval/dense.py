"""Dense retriever facade kept independent from future BM25/hybrid retrievers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .embeddings import Embedder
from .index import DenseIndex, DenseSearchResult

if TYPE_CHECKING:
    from securemail.security.authorization import AuthorizationFilter


@dataclass
class DenseRetriever:
    embedder: Embedder
    index: DenseIndex
    top_k: int = 5
    authorization_filter: AuthorizationFilter | None = None

    def set_authorization_filter(self, authorization_filter: AuthorizationFilter) -> None:
        self.authorization_filter = authorization_filter

    def retrieve(self, question: str, top_k: int | None = None) -> list[DenseSearchResult]:
        limit = self.top_k if top_k is None else top_k
        if not question.strip():
            raise ValueError("question must not be empty")
        allowed_ids = (
            self.authorization_filter.allowed_email_ids(self.index.documents)
            if self.authorization_filter is not None
            else None
        )
        return self.index.search(
            self.embedder.embed([question]),
            top_k=limit,
            allowed_email_ids=allowed_ids,
        )
