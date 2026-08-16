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
from .reranking import (
    CrossEncoderReranker,
    RerankedRetriever,
    RerankedSearchResult,
    Reranker,
    RerankerDependencyError,
    configured_reranker_model,
)

__all__ = [
    "BM25Config",
    "BM25Index",
    "BM25Retriever",
    "CrossEncoderReranker",
    "DenseIndex",
    "DenseRetriever",
    "DenseSearchResult",
    "Embedder",
    "EmbeddingDependencyError",
    "HybridRetriever",
    "RRFConfig",
    "RerankedRetriever",
    "RerankedSearchResult",
    "Reranker",
    "RerankerDependencyError",
    "RetrievalDocument",
    "Retriever",
    "SentenceTransformerEmbedder",
    "build_dense_index",
    "compare_retrieval_results",
    "configured_embedding_model",
    "configured_reranker_model",
    "evaluate_dense_retrieval",
    "evaluate_retriever",
    "load_normalized_jsonl",
    "prepare_document",
    "prepare_documents",
    "rrf_fuse",
    "tokenize",
    "write_evaluation_results",
]
