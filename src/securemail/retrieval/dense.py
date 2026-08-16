"""Dense retriever facade kept independent from future BM25/hybrid retrievers."""

from __future__ import annotations

from dataclasses import dataclass

from .embeddings import Embedder
from .index import DenseIndex, DenseSearchResult


@dataclass
class DenseRetriever:
    embedder: Embedder
    index: DenseIndex
    top_k: int = 5

    def retrieve(self, question: str, top_k: int | None = None) -> list[DenseSearchResult]:
        limit = self.top_k if top_k is None else top_k
        if not question.strip():
            raise ValueError("question must not be empty")
        return self.index.search(self.embedder.embed([question]), top_k=limit)
