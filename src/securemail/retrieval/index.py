"""In-memory and persisted cosine-similarity dense index."""

from __future__ import annotations

import json
from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .documents import RetrievalDocument


@dataclass(frozen=True)
class DenseSearchResult:
    email_id: str
    score: float
    document: RetrievalDocument


class DenseIndex:
    """A simple exact cosine index suitable for the Phase 02 baseline."""

    def __init__(self, documents: list[RetrievalDocument], vectors: np.ndarray):
        matrix = np.asarray(vectors, dtype=np.float32)
        if matrix.ndim != 2 or matrix.shape[0] != len(documents):
            raise ValueError("vectors must be a 2D matrix aligned with documents")
        self.documents = list(documents)
        self.vectors = self._normalize(matrix)

    @staticmethod
    def _normalize(vectors: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return np.divide(vectors, norms, out=np.zeros_like(vectors), where=norms != 0)

    @classmethod
    def build(cls, documents: list[RetrievalDocument], vectors: np.ndarray) -> DenseIndex:
        return cls(documents, vectors)

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
        allowed_email_ids: Collection[str] | None = None,
    ) -> list[DenseSearchResult]:
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")
        candidate_indices = [
            index
            for index, document in enumerate(self.documents)
            if allowed_email_ids is None or document.email_id in allowed_email_ids
        ]
        if not candidate_indices:
            return []
        query = np.asarray(query_vector, dtype=np.float32)
        if query.ndim == 2:
            if query.shape[0] != 1:
                raise ValueError("query_vector must contain one vector")
            query = query[0]
        if query.ndim != 1 or query.shape[0] != self.vectors.shape[1]:
            raise ValueError("query_vector dimensionality does not match the index")
        normalized_query = self._normalize(query.reshape(1, -1))[0]
        scores = self.vectors[candidate_indices] @ normalized_query
        order = np.argsort(-scores, kind="stable")[: min(top_k, len(candidate_indices))]
        return [
            DenseSearchResult(
                email_id=self.documents[candidate_indices[index]].email_id,
                score=float(scores[index]),
                document=self.documents[candidate_indices[index]],
            )
            for index in order
        ]

    def save(self, directory: str | Path) -> Path:
        """Persist vectors and document metadata without storing source emails twice."""

        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        np.save(path / "vectors.npy", self.vectors)
        with (path / "documents.json").open("w", encoding="utf-8") as handle:
            json.dump(
                [
                    {
                        "email_id": document.email_id,
                        "text": document.text,
                        "metadata": document.metadata,
                    }
                    for document in self.documents
                ],
                handle,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        return path

    @classmethod
    def load(cls, directory: str | Path) -> DenseIndex:
        path = Path(directory)
        vectors = np.load(path / "vectors.npy")
        with (path / "documents.json").open(encoding="utf-8") as handle:
            raw_documents = json.load(handle)
        documents = [RetrievalDocument(**item) for item in raw_documents]
        return cls(documents, vectors)
