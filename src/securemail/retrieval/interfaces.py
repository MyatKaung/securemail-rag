"""Shared structural interface for interchangeable retrieval strategies."""

from __future__ import annotations

from typing import Protocol

from .index import DenseSearchResult


class Retriever(Protocol):
    """A retriever that returns ranked documents while preserving email IDs."""

    def retrieve(self, question: str, top_k: int | None = None) -> list[DenseSearchResult]:
        """Return ranked results for a question."""
