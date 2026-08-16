import numpy as np
import pytest

from securemail.ingestion import NormalizedEmail
from securemail.retrieval import (
    DenseIndex,
    DenseRetriever,
    RetrievalDocument,
    prepare_document,
)


class FakeEmbedder:
    model_name = "test/fake-embedder"

    def embed(self, texts):
        vectors = []
        for text in texts:
            lowered = text.lower()
            vectors.append(
                [
                    float("finance" in lowered or "budget" in lowered),
                    float("legal" in lowered or "contract" in lowered),
                    float("vacation" in lowered or "office" in lowered),
                ]
            )
        return np.asarray(vectors, dtype=np.float32)


def document(email_id: str, text: str) -> RetrievalDocument:
    return RetrievalDocument(email_id=email_id, text=text, metadata={})


def test_dense_index_returns_stable_email_ids_in_score_order():
    embedder = FakeEmbedder()
    documents = [
        document("email-finance", "finance budget"),
        document("email-legal", "legal contract"),
        document("email-office", "office vacation"),
    ]
    index = DenseIndex.build(documents, embedder.embed([item.text for item in documents]))

    results = index.search(embedder.embed(["budget"]), top_k=2)

    assert [result.email_id for result in results] == ["email-finance", "email-legal"]
    assert results[0].score > results[1].score


def test_dense_retriever_top_k_is_configurable():
    embedder = FakeEmbedder()
    documents = [document("email-1", "finance"), document("email-2", "legal")]
    index = DenseIndex.build(documents, embedder.embed([item.text for item in documents]))
    retriever = DenseRetriever(embedder=embedder, index=index, top_k=1)

    assert len(retriever.retrieve("finance")) == 1
    assert len(retriever.retrieve("finance", top_k=2)) == 2


def test_dense_index_persists_vectors_and_email_ids(tmp_path):
    embedder = FakeEmbedder()
    documents = [document("email-1", "finance"), document("email-2", "legal")]
    index = DenseIndex.build(documents, embedder.embed([item.text for item in documents]))

    index.save(tmp_path / "index")
    loaded = DenseIndex.load(tmp_path / "index")

    assert [result.email_id for result in loaded.search(embedder.embed(["legal"]))] == [
        "email-2",
        "email-1",
    ]


def test_prepare_document_preserves_email_id_and_retrieval_text():
    email = NormalizedEmail(
        email_id="email-1",
        sender="sender@example.com",
        recipients_to=["receiver@example.com"],
        subject="Budget review",
        body="Please review the budget.",
        mailbox="finance",
        source_path="maildir/finance/inbox/1",
        synthetic_role="finance",
        department="finance",
        access_level="department",
        resource_scope="finance",
    )

    result = prepare_document(email)

    assert result.email_id == "email-1"
    assert "Subject: Budget review" in result.text
    assert "Please review the budget." in result.text


def test_dense_index_rejects_invalid_top_k_and_dimensions():
    index = DenseIndex.build([document("email-1", "finance")], np.ones((1, 3)))

    with pytest.raises(ValueError, match="top_k"):
        index.search(np.ones(3), top_k=0)
    with pytest.raises(ValueError, match="dimensionality"):
        index.search(np.ones(2))
