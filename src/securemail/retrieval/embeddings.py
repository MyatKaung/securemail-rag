"""Swappable embedding interfaces and the configured SentenceTransformer baseline."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

import numpy as np

from securemail.config import PROJECT_ROOT, ConfigurationError, load_yaml_config


class Embedder(Protocol):
    """Minimal embedding interface used by indexing and retrieval."""

    model_name: str

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        """Return one vector per input text."""


class EmbeddingDependencyError(RuntimeError):
    """Raised when the configured SentenceTransformer dependency is unavailable."""


def configured_embedding_model(config_path: str | Path | None = None) -> str:
    """Read the baseline embedding model from ``config/models.yaml``."""

    path = PROJECT_ROOT / "config/models.yaml" if config_path is None else Path(config_path)
    config = load_yaml_config(path)
    try:
        model_name = config["embeddings"]["baseline_model"]
    except (KeyError, TypeError) as exc:
        raise ConfigurationError("config/models.yaml is missing embeddings.baseline_model") from exc
    if not isinstance(model_name, str) or not model_name.strip():
        raise ConfigurationError("embeddings.baseline_model must be a non-empty string")
    return model_name.strip()


class SentenceTransformerEmbedder:
    """Embed text with the configured SentenceTransformers model."""

    def __init__(self, model_name: str | None = None, model: object | None = None):
        self.model_name = model_name or configured_embedding_model()
        if model is not None:
            self._model = model
            return
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise EmbeddingDependencyError(
                "sentence-transformers is required for the dense retrieval baseline"
            ) from exc
        self._model = SentenceTransformer(self.model_name)

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        values = list(texts)
        if not values:
            return np.empty((0, 0), dtype=np.float32)
        vectors = self._model.encode(
            values,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        matrix = np.asarray(vectors, dtype=np.float32)
        if matrix.ndim == 1:
            matrix = matrix.reshape(1, -1)
        return matrix
