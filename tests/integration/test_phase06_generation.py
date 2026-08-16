import numpy as np

from securemail.generation import (
    STRUCTURED_GROUNDED_STRATEGY,
    PermissionAwareGenerationPipeline,
)
from securemail.retrieval.bm25 import BM25Retriever
from securemail.retrieval.dense import DenseRetriever
from securemail.retrieval.documents import RetrievalDocument
from securemail.retrieval.hybrid import HybridRetriever, RRFConfig
from securemail.retrieval.index import DenseIndex
from securemail.retrieval.reranking import CrossEncoderReranker, RerankedRetriever
from securemail.security import AuthorizationFilter, PrincipalContext, SyntheticRBACPolicy


class FakeEmbedder:
    model_name = "test-embedder"

    def embed(self, texts: list[str]) -> np.ndarray:
        return np.asarray(
            [[float("finance" in text), float("legal" in text)] for text in texts],
            dtype=np.float32,
        )


class FakeCrossEncoder:
    def predict(self, pairs: list[tuple[str, str]]) -> list[float]:
        return [float("finance" in document) for _, document in pairs]


class FakeGenerator:
    def __init__(self) -> None:
        self.prompts: list[str] = []
        self.system_prompts: list[str] = []

    def generate(self, prompt: str, *, system_prompt: str, **kwargs: object) -> str:
        del kwargs
        self.prompts.append(prompt)
        self.system_prompts.append(system_prompt)
        return (
            "Answer: The finance message is supported.\nUncertainty: None\nSources: [finance-email]"
        )


def test_permission_aware_hybrid_reranker_prompt_generation_boundary() -> None:
    documents = [
        RetrievalDocument(
            "finance-email",
            "Subject: finance plan\nBody: Finance evidence.",
            {"department": "finance", "access_level": "department", "resource_scope": "finance"},
        ),
        RetrievalDocument(
            "legal-email",
            "Subject: legal plan\nBody: Restricted legal evidence.",
            {"department": "legal", "access_level": "department", "resource_scope": "legal"},
        ),
    ]
    embedder = FakeEmbedder()
    index = DenseIndex(documents, embedder.embed([document.text for document in documents]))
    authorization_filter = AuthorizationFilter(
        PrincipalContext("finance", "finance", "department", "finance"),
        SyntheticRBACPolicy(),
    )
    dense = DenseRetriever(embedder, index, top_k=2, authorization_filter=authorization_filter)
    bm25 = BM25Retriever(documents, top_k=2, authorization_filter=authorization_filter)
    hybrid = HybridRetriever(
        dense,
        bm25,
        top_k=2,
        config=RRFConfig(candidate_k=2),
        authorization_filter=authorization_filter,
    )
    reranked = RerankedRetriever(
        hybrid,
        CrossEncoderReranker(model=FakeCrossEncoder()),
        candidate_k=2,
        final_k=2,
        authorization_filter=authorization_filter,
    )
    generator = FakeGenerator()
    response = PermissionAwareGenerationPipeline(
        reranked,
        generator,
        authorization_filter,
        STRUCTURED_GROUNDED_STRATEGY,
    ).answer("What is the finance plan?", top_k=2)

    assert response.source_email_ids == ["finance-email"]
    assert "finance-email" in generator.prompts[0]
    assert "legal-email" not in generator.prompts[0]
    assert generator.system_prompts[0] == STRUCTURED_GROUNDED_STRATEGY.system_prompt
