import numpy as np

from securemail.retrieval.bm25 import BM25Retriever
from securemail.retrieval.dense import DenseRetriever
from securemail.retrieval.documents import RetrievalDocument
from securemail.retrieval.hybrid import HybridRetriever, RRFConfig
from securemail.retrieval.index import DenseIndex


class FakeEmbedder:
    model_name = "test-embedder"

    def embed(self, texts: list[str]) -> np.ndarray:
        vectors = []
        for text in texts:
            lower = text.casefold()
            vectors.append(
                [float("alpha" in lower), float("beta" in lower), float("gamma" in lower)]
            )
        return np.asarray(vectors, dtype=np.float32)


def test_same_question_runs_through_dense_bm25_and_hybrid() -> None:
    documents = [
        RetrievalDocument("email-alpha", "Subject: alpha plan", {}),
        RetrievalDocument("email-beta", "Subject: beta plan", {}),
        RetrievalDocument("email-gamma", "Subject: gamma plan", {}),
    ]
    embedder = FakeEmbedder()
    index = DenseIndex(documents, embedder.embed([item.text for item in documents]))
    dense = DenseRetriever(embedder=embedder, index=index, top_k=2)
    bm25 = BM25Retriever(documents, top_k=2)
    hybrid = HybridRetriever(dense, bm25, top_k=2, config=RRFConfig(candidate_k=2))

    dense_ids = [item.email_id for item in dense.retrieve("alpha", top_k=2)]
    bm25_ids = [item.email_id for item in bm25.retrieve("alpha", top_k=2)]
    hybrid_ids = [item.email_id for item in hybrid.retrieve("alpha", top_k=2)]
    assert dense_ids[0] == "email-alpha"
    assert bm25_ids[0] == "email-alpha"
    assert hybrid_ids[0] == "email-alpha"
