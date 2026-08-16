"""Swappable cross-encoder reranking over a wider hybrid candidate set."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

import numpy as np

from securemail.config import PROJECT_ROOT, ConfigurationError, load_yaml_config

from .documents import RetrievalDocument
from .index import DenseSearchResult
from .interfaces import Retriever

if TYPE_CHECKING:
    from securemail.security.authorization import AuthorizationFilter


class CrossEncoderModel(Protocol):
    """Minimal model boundary used by the reranker and its test doubles."""

    def predict(self, sentence_pairs: Sequence[tuple[str, str]]) -> Sequence[float]:
        """Return one relevance score per query/document pair."""


class RerankerDependencyError(RuntimeError):
    """Raised when the configured cross-encoder dependency is unavailable."""


def configured_reranker_model(config_path: str | Path | None = None) -> str:
    """Read the reranker model from ``config/models.yaml``."""

    path = PROJECT_ROOT / "config/models.yaml" if config_path is None else Path(config_path)
    config = load_yaml_config(path)
    try:
        model_name = config["reranker"]["baseline_model"]
    except (KeyError, TypeError) as exc:
        raise ConfigurationError("config/models.yaml is missing reranker.baseline_model") from exc
    if not isinstance(model_name, str) or not model_name.strip():
        raise ConfigurationError("reranker.baseline_model must be a non-empty string")
    return model_name.strip()


@dataclass(frozen=True)
class RerankedSearchResult:
    """A result retaining both the candidate retrieval and reranker evidence."""

    email_id: str
    document: RetrievalDocument
    retrieval_score: float
    retrieval_rank: int
    reranker_score: float


class Reranker(Protocol):
    """Common interface for swappable candidate rerankers."""

    def rerank(
        self,
        query: str,
        candidates: Sequence[DenseSearchResult],
        *,
        final_k: int,
    ) -> list[RerankedSearchResult]:
        """Rerank candidates and return at most ``final_k`` results."""


class CrossEncoderReranker:
    """Score the original query against each candidate's original text."""

    def __init__(
        self,
        model_name: str | None = None,
        model: CrossEncoderModel | None = None,
    ) -> None:
        self.model_name = model_name or configured_reranker_model()
        if model is not None:
            self._model = model
            return
        try:
            from sentence_transformers import CrossEncoder
        except ImportError as exc:
            raise RerankerDependencyError(
                "sentence-transformers is required for cross-encoder reranking"
            ) from exc
        self._model = CrossEncoder(self.model_name)

    def rerank(
        self,
        query: str,
        candidates: Sequence[DenseSearchResult],
        *,
        final_k: int,
    ) -> list[RerankedSearchResult]:
        if final_k <= 0:
            raise ValueError("final_k must be greater than zero")
        if not candidates:
            return []
        pairs = [(query, candidate.document.text) for candidate in candidates]
        scores = np.asarray(self._model.predict(pairs), dtype=float).reshape(-1)
        if len(scores) != len(candidates):
            raise ValueError("reranker must return one score per candidate")
        ranked = sorted(
            enumerate(zip(candidates, scores, strict=True)),
            key=lambda item: (-float(item[1][1]), item[0]),
        )
        return [
            RerankedSearchResult(
                email_id=candidate.email_id,
                document=candidate.document,
                retrieval_score=float(candidate.score),
                retrieval_rank=original_index + 1,
                reranker_score=float(score),
            )
            for original_index, (candidate, score) in ranked[:final_k]
        ]


class RerankedRetriever:
    """Compose a candidate retriever with a reranker."""

    def __init__(
        self,
        candidate_retriever: Retriever,
        reranker: Reranker,
        *,
        candidate_k: int = 20,
        final_k: int = 5,
        authorization_filter: AuthorizationFilter | None = None,
    ) -> None:
        if candidate_k <= 0:
            raise ValueError("candidate_k must be greater than zero")
        if final_k <= 0:
            raise ValueError("final_k must be greater than zero")
        self.candidate_retriever = candidate_retriever
        self.reranker = reranker
        self.candidate_k = candidate_k
        self.final_k = final_k
        self.authorization_filter = authorization_filter
        if authorization_filter is not None:
            setter = getattr(candidate_retriever, "set_authorization_filter", None)
            if setter is None:
                raise TypeError("candidate retriever must support pre-retrieval authorization")
            setter(authorization_filter)

    def retrieve(self, question: str, top_k: int | None = None) -> list[RerankedSearchResult]:
        requested_k = self.final_k if top_k is None else top_k
        if requested_k <= 0:
            raise ValueError("top_k must be greater than zero")
        candidates = self.candidate_retriever.retrieve(question, top_k=self.candidate_k)
        return self.reranker.rerank(question, candidates, final_k=requested_k)
