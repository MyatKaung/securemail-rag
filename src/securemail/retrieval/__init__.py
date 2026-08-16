"""Retrieval interfaces, the dense baseline, BM25, and RRF hybrid search."""

from .bm25 import BM25Config, BM25Index, BM25Retriever, tokenize
from .dense import DenseRetriever
from .documents import RetrievalDocument, prepare_document, prepare_documents
from .embeddings import (
    Embedder,
    EmbeddingDependencyError,
    SentenceTransformerEmbedder,
    configured_embedding_model,
)
from .evaluation import (
    compare_retrieval_results,
    evaluate_dense_retrieval,
    evaluate_retriever,
    write_evaluation_results,
)
from .hybrid import HybridRetriever, RRFConfig, rrf_fuse
from .index import DenseIndex, DenseSearchResult
from .indexing import build_dense_index, load_normalized_jsonl
from .interfaces import Retriever

__all__ = [
    "BM25Config",
    "BM25Index",
    "BM25Retriever",
    "DenseIndex",
    "DenseRetriever",
    "DenseSearchResult",
    "Embedder",
    "EmbeddingDependencyError",
    "HybridRetriever",
    "RRFConfig",
    "RetrievalDocument",
    "Retriever",
    "SentenceTransformerEmbedder",
    "build_dense_index",
    "compare_retrieval_results",
    "configured_embedding_model",
    "evaluate_dense_retrieval",
    "evaluate_retriever",
    "load_normalized_jsonl",
    "prepare_document",
    "prepare_documents",
    "rrf_fuse",
    "tokenize",
    "write_evaluation_results",
]
