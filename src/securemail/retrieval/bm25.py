"""Deterministic BM25 retrieval over prepared email documents."""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np
from rank_bm25 import BM25Okapi

from .documents import RetrievalDocument
from .index import DenseSearchResult

TOKEN_PATTERN = re.compile(r"\b\w+\b", re.UNICODE)
Tokenizer = Callable[[str], list[str]]


def tokenize(text: str) -> list[str]:
    """Tokenize email text consistently for indexing and querying."""

    return [match.group(0).casefold() for match in TOKEN_PATTERN.finditer(text or "")]


@dataclass(frozen=True)
class BM25Config:
    """BM25 parameters kept explicit for reproducible experiments."""

    k1: float = 1.5
    b: float = 0.75

    def __post_init__(self) -> None:
        if self.k1 < 0:
            raise ValueError("k1 must be non-negative")
        if not 0 <= self.b <= 1:
            raise ValueError("b must be between zero and one")


class BM25Index:
    """In-memory sparse index that maps BM25 ranks back to email documents."""

    def __init__(
        self,
        documents: Sequence[RetrievalDocument],
        *,
        config: BM25Config | None = None,
        tokenizer: Tokenizer = tokenize,
    ) -> None:
        self.documents = tuple(documents)
        self.tokenizer = tokenizer
        self.config = config or BM25Config()
        self.tokenized_documents = tuple(self.tokenizer(doc.text) for doc in self.documents)
        self._bm25 = (
            BM25Okapi(
                list(self.tokenized_documents),
                k1=self.config.k1,
                b=self.config.b,
            )
            if self.tokenized_documents
            else None
        )

    def search(self, query: str, *, top_k: int) -> list[DenseSearchResult]:
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")
        if self._bm25 is None:
            return []
        query_tokens = self.tokenizer(query)
        if not query_tokens:
            return []
        scores = np.asarray(self._bm25.get_scores(query_tokens), dtype=float)
        indexed_tokens = {token for document in self.tokenized_documents for token in document}
        if scores.size == 0 or not indexed_tokens.intersection(query_tokens):
            return []
        # Input order is the deterministic tie-breaker. This is stable across runs
        # and keeps equal-score emails from being reordered by a hash/set operation.
        ranked_indices = sorted(range(len(self.documents)), key=lambda i: (-scores[i], i))
        return [
            DenseSearchResult(
                email_id=self.documents[index].email_id,
                score=float(scores[index]),
                document=self.documents[index],
            )
            for index in ranked_indices[:top_k]
        ]


class BM25Retriever:
    """Retriever wrapper around :class:`BM25Index` with a configurable default k."""

    def __init__(
        self,
        documents: Sequence[RetrievalDocument] | None = None,
        *,
        index: BM25Index | None = None,
        top_k: int = 5,
        config: BM25Config | None = None,
        tokenizer: Tokenizer = tokenize,
    ) -> None:
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")
        if index is not None and documents is not None:
            raise ValueError("provide documents or index, not both")
        self.index = index or BM25Index(documents or (), config=config, tokenizer=tokenizer)
        self.top_k = top_k

    def retrieve(self, question: str, top_k: int | None = None) -> list[DenseSearchResult]:
        requested_k = self.top_k if top_k is None else top_k
        return self.index.search(question, top_k=requested_k)
