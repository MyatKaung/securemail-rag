from securemail.retrieval.bm25 import BM25Config, BM25Index, BM25Retriever, tokenize
from securemail.retrieval.documents import RetrievalDocument


def document(email_id: str, text: str) -> RetrievalDocument:
    return RetrievalDocument(email_id=email_id, text=text, metadata={})


def test_tokenizer_is_case_insensitive_and_deterministic() -> None:
    assert tokenize("Subject: ENRON-42, status!") == ["subject", "enron", "42", "status"]


def test_bm25_indexes_and_scores_matching_terms() -> None:
    index = BM25Index(
        [
            document("a", "project alpha budget"),
            document("b", "project beta schedule"),
            document("c", "project gamma forecast"),
        ]
    )
    results = index.search("alpha budget", top_k=2)
    assert [result.email_id for result in results] == ["a", "b"]
    assert results[0].score > 0


def test_bm25_ranking_and_ties_are_deterministic() -> None:
    docs = [document("first", "common"), document("second", "common")]
    retriever = BM25Retriever(docs, config=BM25Config())
    assert [result.email_id for result in retriever.retrieve("common", top_k=2)] == [
        "first",
        "second",
    ]
    assert [result.email_id for result in retriever.retrieve("common", top_k=2)] == [
        "first",
        "second",
    ]


def test_bm25_empty_and_no_result_cases_are_safe() -> None:
    empty = BM25Retriever([])
    assert empty.retrieve("anything") == []
    retriever = BM25Retriever([document("a", "alpha")])
    assert retriever.retrieve("unseen term") == []


def test_bm25_rejects_invalid_parameters() -> None:
    try:
        BM25Config(b=-0.1)
    except ValueError as error:
        assert "b" in str(error)
    else:
        raise AssertionError("invalid b should fail")
