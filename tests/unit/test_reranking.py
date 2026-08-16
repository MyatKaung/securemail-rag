import pytest

from securemail.retrieval.documents import RetrievalDocument
from securemail.retrieval.index import DenseSearchResult
from securemail.retrieval.reranking import (
    CrossEncoderReranker,
    RerankedRetriever,
    configured_reranker_model,
)


def candidate(email_id: str, score: float) -> DenseSearchResult:
    return DenseSearchResult(
        email_id=email_id,
        score=score,
        document=RetrievalDocument(
            email_id=email_id,
            text=f"body for {email_id}",
            metadata={"subject": f"subject {email_id}"},
        ),
    )


class FakeCrossEncoder:
    def __init__(self, scores: list[float]) -> None:
        self.scores = scores
        self.pairs: list[tuple[str, str]] = []

    def predict(self, sentence_pairs: list[tuple[str, str]]) -> list[float]:
        self.pairs = list(sentence_pairs)
        return self.scores


def test_reranker_uses_query_and_original_text_and_preserves_source_fields() -> None:
    model = FakeCrossEncoder([0.2, 0.9])
    reranker = CrossEncoderReranker(model=model)
    results = reranker.rerank(
        "original question",
        [candidate("first", 0.7), candidate("second", 0.6)],
        final_k=2,
    )
    assert model.pairs == [
        ("original question", "body for first"),
        ("original question", "body for second"),
    ]
    assert [result.email_id for result in results] == ["second", "first"]
    assert results[0].retrieval_score == 0.6
    assert results[0].retrieval_rank == 2
    assert results[0].reranker_score == 0.9
    assert results[0].document.metadata["subject"] == "subject second"


def test_reranking_is_deterministic_and_ties_keep_candidate_order() -> None:
    candidates = [candidate("first", 0.7), candidate("second", 0.6)]
    reranker = CrossEncoderReranker(model=FakeCrossEncoder([0.5, 0.5]))
    assert [item.email_id for item in reranker.rerank("q", candidates, final_k=2)] == [
        "first",
        "second",
    ]


def test_reranking_truncates_to_final_k_and_handles_empty_candidates() -> None:
    reranker = CrossEncoderReranker(model=FakeCrossEncoder([0.1, 0.8, 0.4]))
    results = reranker.rerank(
        "q",
        [candidate("a", 1), candidate("b", 2), candidate("c", 3)],
        final_k=2,
    )
    assert [item.email_id for item in results] == ["b", "c"]
    assert reranker.rerank("q", [], final_k=5) == []


def test_reranker_rejects_invalid_final_k() -> None:
    reranker = CrossEncoderReranker(model=FakeCrossEncoder([]))
    with pytest.raises(ValueError, match="final_k"):
        reranker.rerank("q", [], final_k=0)


def test_configured_reranker_model_matches_model_strategy() -> None:
    assert configured_reranker_model() == "cross-encoder/ms-marco-MiniLM-L-6-v2"


class StubCandidateRetriever:
    def __init__(self, candidates: list[DenseSearchResult]) -> None:
        self.candidates = candidates
        self.requested_k: int | None = None

    def retrieve(self, question: str, top_k: int | None = None) -> list[DenseSearchResult]:
        del question
        self.requested_k = top_k
        return self.candidates[: top_k or len(self.candidates)]


def test_reranked_retriever_requests_wide_candidates_and_returns_final_k() -> None:
    candidate_retriever = StubCandidateRetriever(
        [candidate("a", 1), candidate("b", 2), candidate("c", 3)]
    )
    reranked = RerankedRetriever(
        candidate_retriever,
        CrossEncoderReranker(model=FakeCrossEncoder([0.1, 0.9, 0.2])),
        candidate_k=3,
        final_k=2,
    )
    results = reranked.retrieve("question")
    assert candidate_retriever.requested_k == 3
    assert [item.email_id for item in results] == ["b", "c"]
