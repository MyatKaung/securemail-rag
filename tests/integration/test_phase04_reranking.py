import numpy as np

from securemail.retrieval.bm25 import BM25Retriever
from securemail.retrieval.dense import DenseRetriever
from securemail.retrieval.documents import RetrievalDocument
from securemail.retrieval.hybrid import HybridRetriever, RRFConfig
from securemail.retrieval.index import DenseIndex
from securemail.retrieval.reranking import CrossEncoderReranker, RerankedRetriever


class FakeEmbedder:
    model_name = "test-embedder"

    def embed(self, texts: list[str]) -> np.ndarray:
        return np.asarray(
            [
                [float("alpha" in text.casefold()), float("beta" in text.casefold())]
                for text in texts
            ],
            dtype=np.float32,
        )


class QueryAwareCrossEncoder:
    def predict(self, sentence_pairs: list[tuple[str, str]]) -> list[float]:
        return [float("best" in document_text) for _, document_text in sentence_pairs]


def test_hybrid_candidates_are_reranked_to_final_top_five() -> None:
    documents = [
        RetrievalDocument("email-alpha", "alpha ordinary", {}),
        RetrievalDocument("email-best", "alpha best", {}),
        RetrievalDocument("email-beta", "beta ordinary", {}),
    ]
    embedder = FakeEmbedder()
    index = DenseIndex(documents, embedder.embed([document.text for document in documents]))
    dense = DenseRetriever(embedder=embedder, index=index, top_k=3)
    bm25 = BM25Retriever(documents, top_k=3)
    hybrid = HybridRetriever(dense, bm25, top_k=5, config=RRFConfig(candidate_k=3))
    reranked = RerankedRetriever(
        hybrid,
        CrossEncoderReranker(model=QueryAwareCrossEncoder()),
        candidate_k=3,
        final_k=5,
    )

    results = reranked.retrieve("alpha", top_k=5)
    assert len(results) == 3
    assert results[0].email_id == "email-best"
    assert results[0].reranker_score == 1.0
    assert all(result.retrieval_rank <= 3 for result in results)
