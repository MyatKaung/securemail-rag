"""Retrieval interfaces and the Phase 02 dense baseline."""

from .dense import DenseRetriever
from .documents import RetrievalDocument, prepare_document, prepare_documents
from .embeddings import (
    Embedder,
    EmbeddingDependencyError,
    SentenceTransformerEmbedder,
    configured_embedding_model,
)
from .evaluation import evaluate_dense_retrieval, write_evaluation_results
from .index import DenseIndex, DenseSearchResult
from .indexing import build_dense_index, load_normalized_jsonl

__all__ = [
    "DenseIndex",
    "DenseRetriever",
    "DenseSearchResult",
    "Embedder",
    "EmbeddingDependencyError",
    "RetrievalDocument",
    "SentenceTransformerEmbedder",
    "build_dense_index",
    "configured_embedding_model",
    "evaluate_dense_retrieval",
    "load_normalized_jsonl",
    "prepare_document",
    "prepare_documents",
    "write_evaluation_results",
]
