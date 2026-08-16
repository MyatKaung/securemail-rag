from pathlib import Path

import numpy as np

from securemail.evaluation import RetrievalGroundTruthRecord, load_records
from securemail.generation import BasicDenseRAG
from securemail.ingestion import NormalizedEmail
from securemail.retrieval import (
    DenseIndex,
    DenseRetriever,
    load_normalized_jsonl,
    prepare_documents,
)


class FakeEmbedder:
    model_name = "test/fake-embedder"

    def embed(self, texts):
        return np.asarray(
            [[1.0, 0.0] if "budget" in text.lower() else [0.0, 1.0] for text in texts],
            dtype=np.float32,
        )


class FakeGenerator:
    def __init__(self):
        self.prompts = []

    def generate(self, prompt):
        self.prompts.append(prompt)
        return "The evidence discusses the budget. [enron-budget]"


def email(email_id, subject, body):
    return NormalizedEmail(
        email_id=email_id,
        sender="sender@example.com",
        subject=subject,
        body=body,
        mailbox="general",
        source_path=f"maildir/general/inbox/{email_id}",
        synthetic_role="general",
        department="general",
        access_level="standard",
        resource_scope="shared",
    )


def test_question_retrieval_prompt_and_grounded_generation_are_composable():
    embedder = FakeEmbedder()
    documents = prepare_documents(
        [
            email("enron-budget", "Budget review", "The budget is due Friday."),
            email("enron-legal", "Contract", "Review the contract."),
        ]
    )
    index = DenseIndex.build(documents, embedder.embed([document.text for document in documents]))
    retriever = DenseRetriever(embedder=embedder, index=index, top_k=1)
    generator = FakeGenerator()
    rag = BasicDenseRAG(retriever, generator)

    response = rag.answer("What is the budget?", top_k=1)

    assert response.source_email_ids == ["enron-budget"]
    assert response.answer.startswith("The evidence discusses")
    assert generator.prompts
    assert "enron-budget" in generator.prompts[0]
    assert "The budget is due Friday." in generator.prompts[0]


def test_phase02_ground_truth_ids_exist_in_the_500_email_corpus():
    root = Path(__file__).resolve().parents[2]
    corpus_ids = {
        record.email_id
        for record in load_normalized_jsonl(root / "data/sample/enron_dev_500.jsonl")
    }
    questions = load_records(
        root / "evals/datasets/retrieval_ground_truth.phase02.json",
        RetrievalGroundTruthRecord,
    )

    assert len(questions) == 20
    assert all(set(item.relevant_email_ids) <= corpus_ids for item in questions)
