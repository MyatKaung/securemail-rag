from securemail.retrieval.documents import RetrievalDocument
from securemail.retrieval.hybrid import HybridRetriever, RRFConfig, rrf_fuse
from securemail.retrieval.index import DenseSearchResult


def result(email_id: str, score: float = 1.0) -> DenseSearchResult:
    return DenseSearchResult(
        email_id=email_id,
        score=score,
        document=RetrievalDocument(email_id=email_id, text=email_id, metadata={}),
    )


def test_rrf_uses_one_based_rank_formula() -> None:
    fused = rrf_fuse([[result("a"), result("b")], [result("b"), result("a")]], config=RRFConfig(1))
    assert [item.email_id for item in fused] == ["a", "b"]
    assert fused[0].score == 1 / 2 + 1 / 3


def test_rrf_tie_breaks_by_first_seen_then_email_id() -> None:
    fused = rrf_fuse([[result("b")], [result("a")]], config=RRFConfig(1))
    assert [item.email_id for item in fused] == ["b", "a"]


def test_rrf_empty_rankings_return_empty() -> None:
    assert rrf_fuse([[], []]) == []


class StubRetriever:
    def __init__(self, ids: list[str]) -> None:
        self.ids = ids

    def retrieve(self, question: str, top_k: int | None = None) -> list[DenseSearchResult]:
        del question
        return [result(email_id) for email_id in self.ids[: top_k or len(self.ids)]]


def test_hybrid_runs_both_retrievers_with_shared_contract() -> None:
    hybrid = HybridRetriever(
        StubRetriever(["dense-a", "shared"]),
        StubRetriever(["bm25-a", "shared"]),
        config=RRFConfig(rank_constant=1, candidate_k=2),
    )
    assert [item.email_id for item in hybrid.retrieve("question", top_k=3)] == [
        "shared",
        "dense-a",
        "bm25-a",
    ]
