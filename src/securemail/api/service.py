"""Application service wiring for the production Phase 07 RAG path."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Protocol

from securemail.config import PROJECT_ROOT, ConfigurationError
from securemail.generation import (
    BASIC_GROUNDED_V1,
    OpenRouterGenerationClient,
    PermissionAwareGenerationPipeline,
    get_prompt_strategy,
)
from securemail.monitoring import (
    MonitoringStore,
    RequestTelemetry,
    SQLiteMonitoringStore,
    ensure_request_id,
)
from securemail.monitoring.logging import log_event
from securemail.monitoring.timing import (
    PhaseTimings,
    TimedGenerationClient,
    TimedReranker,
    TimedRetriever,
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
REQUIRED_RUNTIME_FILES = (
    DATA_PATH,
    PROJECT_ROOT / "config/app.yaml",
    PROJECT_ROOT / "config/models.yaml",
)
RETRIEVAL_METHOD = "hybrid+cross_encoder_reranker"
CANDIDATE_K = 20
FINAL_K = 5


class QueryServiceError(RuntimeError):
    """Safe public error for retrieval or generation failures."""


class MalformedPrincipalError(ValueError):
    """Raised when a request principal cannot be represented by the policy."""


def validate_runtime_assets(data_path: str | Path = DATA_PATH) -> None:
    """Fail clearly when a fresh checkout lacks required non-secret runtime files."""

    required = (*REQUIRED_RUNTIME_FILES[1:], Path(data_path))
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise ConfigurationError(
            "required runtime data/config is missing: "
            + ", ".join(missing)
            + "; run `make ingest` for the normalized development data"
        )


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
        monitoring_store: MonitoringStore | None = None,
    ) -> None:
        self.index = index
        self.embedder = embedder
        self.reranker = reranker
        self.generator = generator
        self.candidate_k = candidate_k
        self.final_k = final_k
        self.monitoring_store = monitoring_store

    @classmethod
    def from_defaults(
        cls,
        data_path: str | Path = DATA_PATH,
        monitoring_store: MonitoringStore | None = None,
    ) -> DefaultRAGService:
        """Load production dependencies lazily; fail clearly if OpenRouter is unavailable."""

        validate_runtime_assets(data_path)
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
            monitoring_store=monitoring_store or SQLiteMonitoringStore(),
        )

    def query(self, request: QueryRequest) -> QueryResponse:
        request_id = ensure_request_id()
        started_at = datetime.now(UTC)
        started = perf_counter()
        timings = PhaseTimings()
        permission_denied = False
        refused = False
        insufficient_evidence = False
        status_code = 200
        log_event("rag_request_started")
        try:
            try:
                principal = PrincipalContext(**request.principal.model_dump())
            except (TypeError, ValueError) as exc:
                status_code = 422
                raise MalformedPrincipalError("malformed principal context") from exc

            authorization_filter = AuthorizationFilter(principal, SyntheticRBACPolicy())
            log_event("authorization_filter_applied")
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
                TimedRetriever(hybrid, timings),
                TimedReranker(self.reranker, timings),
                candidate_k=self.candidate_k,
                final_k=self.final_k,
                authorization_filter=authorization_filter,
            )
            result = PermissionAwareGenerationPipeline(
                reranked,
                TimedGenerationClient(self.generator, timings),
                authorization_filter,
                get_prompt_strategy(BASIC_GROUNDED_V1),
            ).answer(request.question, top_k=self.final_k)
            refused = result.parsed.refused
            insufficient_evidence = result.parsed.refused
            return QueryResponse(
                request_id=request_id,
                answer=result.answer,
                source_email_ids=result.source_email_ids,
                retrieval_method=RETRIEVAL_METHOD,
                retrieved_evidence_count=len(result.retrieved),
                refused=refused,
                insufficient_evidence=insufficient_evidence,
                uncertainty=result.parsed.uncertainty,
            )
        except AuthorizationError:
            permission_denied = True
            status_code = 403
            raise
        except (MalformedPrincipalError, QueryServiceError):
            raise
        except Exception as exc:
            status_code = 502
            raise QueryServiceError("secure retrieval or generation failed") from exc
        finally:
            telemetry = RequestTelemetry(
                request_id=request_id,
                started_at=started_at.isoformat(),
                total_latency_ms=(perf_counter() - started) * 1000,
                retrieval_latency_ms=timings.retrieval_latency_ms,
                reranking_latency_ms=timings.reranking_latency_ms,
                llm_latency_ms=timings.llm_latency_ms,
                permission_denied=permission_denied,
                refused=refused,
                insufficient_evidence=insufficient_evidence,
                status_code=status_code,
            )
            if self.monitoring_store is not None:
                try:
                    self.monitoring_store.record_request(telemetry)
                except Exception as exc:  # noqa: BLE001  # telemetry must never break the RAG response
                    log_event("telemetry_write_failed", error_type=type(exc).__name__)
            log_event(
                "rag_request_completed",
                status_code=status_code,
                total_latency_ms=round(telemetry.total_latency_ms, 3),
                retrieval_latency_ms=round(telemetry.retrieval_latency_ms, 3),
                reranking_latency_ms=round(telemetry.reranking_latency_ms, 3),
                llm_latency_ms=round(telemetry.llm_latency_ms, 3),
                permission_denied=permission_denied,
                refused=refused,
            )


def build_default_service(monitoring_store: MonitoringStore | None = None) -> DefaultRAGService:
    """Factory kept separate so API tests can inject a fully offline service."""

    try:
        return DefaultRAGService.from_defaults(monitoring_store=monitoring_store)
    except ConfigurationError:
        raise
    except Exception as exc:
        raise QueryServiceError("secure RAG service initialization failed") from exc
