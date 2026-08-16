"""Application service wiring for the production Phase 07 RAG path."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from securemail.config import PROJECT_ROOT, ConfigurationError
from securemail.generation import (
    BASIC_GROUNDED_V1,
    OpenRouterGenerationClient,
    PermissionAwareGenerationPipeline,
    get_prompt_strategy,
)
from securemail.retrieval.bm25 import BM25Config, BM25Retriever
from securemail.retrieval.dense import DenseRetriever
from securemail.retrieval.embeddings import SentenceTransformerEmbedder
from securemail.retrieval.hybrid import HybridRetriever, RRFConfig
from securemail.retrieval.index import DenseIndex
from securemail.retrieval.indexing import build_dense_index
from securemail.retrieval.reranking import CrossEncoderReranker, RerankedRetriever
from securemail.security import (
    AuthorizationError,
    AuthorizationFilter,
    PrincipalContext,
    SyntheticRBACPolicy,
)

from .schemas import QueryRequest, QueryResponse

DATA_PATH = PROJECT_ROOT / "data/sample/enron_dev_500.jsonl"
RETRIEVAL_METHOD = "hybrid+cross_encoder_reranker"
CANDIDATE_K = 20
FINAL_K = 5


class QueryServiceError(RuntimeError):
    """Safe public error for retrieval or generation failures."""


class MalformedPrincipalError(ValueError):
    """Raised when a request principal cannot be represented by the policy."""


class QueryService(Protocol):
    def query(self, request: QueryRequest) -> QueryResponse:
        """Run one secure end-to-end RAG query."""


class DefaultRAGService:
    """Compose the existing production retrieval and generation components."""

    def __init__(
        self,
        *,
        index: DenseIndex,
        embedder: object,
        reranker: object,
        generator: object,
        candidate_k: int = CANDIDATE_K,
        final_k: int = FINAL_K,
    ) -> None:
        self.index = index
        self.embedder = embedder
        self.reranker = reranker
        self.generator = generator
        self.candidate_k = candidate_k
        self.final_k = final_k

    @classmethod
    def from_defaults(cls, data_path: str | Path = DATA_PATH) -> DefaultRAGService:
        """Load production dependencies lazily; fail clearly if OpenRouter is unavailable."""

        # Validate credentials before loading heavyweight local models.
        generator = OpenRouterGenerationClient()
        embedder = SentenceTransformerEmbedder()
        index = build_dense_index(data_path, embedder)
        reranker = CrossEncoderReranker()
        return cls(
            index=index,
            embedder=embedder,
            reranker=reranker,
            generator=generator,
        )

    def query(self, request: QueryRequest) -> QueryResponse:
        try:
            principal = PrincipalContext(**request.principal.model_dump())
        except (TypeError, ValueError) as exc:
            raise MalformedPrincipalError("malformed principal context") from exc

        authorization_filter = AuthorizationFilter(principal, SyntheticRBACPolicy())
        try:
            # These wrappers are request-scoped so a principal cannot mutate a
            # shared retriever's authorization context during concurrent calls.
            dense = DenseRetriever(
                self.embedder,
                self.index,
                top_k=self.candidate_k,
                authorization_filter=authorization_filter,
            )
            bm25 = BM25Retriever(
                self.index.documents,
                top_k=self.candidate_k,
                config=BM25Config(),
                authorization_filter=authorization_filter,
            )
            hybrid = HybridRetriever(
                dense,
                bm25,
                top_k=self.final_k,
                config=RRFConfig(candidate_k=self.candidate_k),
                authorization_filter=authorization_filter,
            )
            reranked = RerankedRetriever(
                hybrid,
                self.reranker,
                candidate_k=self.candidate_k,
                final_k=self.final_k,
                authorization_filter=authorization_filter,
            )
            result = PermissionAwareGenerationPipeline(
                reranked,
                self.generator,
                authorization_filter,
                get_prompt_strategy(BASIC_GROUNDED_V1),
            ).answer(request.question, top_k=self.final_k)
        except AuthorizationError:
            raise
        except Exception as exc:
            raise QueryServiceError("secure retrieval or generation failed") from exc

        return QueryResponse(
            answer=result.answer,
            source_email_ids=result.source_email_ids,
            retrieval_method=RETRIEVAL_METHOD,
            retrieved_evidence_count=len(result.retrieved),
            refused=result.parsed.refused,
            insufficient_evidence=result.parsed.refused,
            uncertainty=result.parsed.uncertainty,
        )


def build_default_service() -> DefaultRAGService:
    """Factory kept separate so API tests can inject a fully offline service."""

    try:
        return DefaultRAGService.from_defaults()
    except ConfigurationError:
        raise
    except Exception as exc:
        raise QueryServiceError("secure RAG service initialization failed") from exc
