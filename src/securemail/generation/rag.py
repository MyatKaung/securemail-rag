"""Basic question-to-dense-retrieval-to-grounded-generation flow."""

from __future__ import annotations

from dataclasses import dataclass

from securemail.retrieval import DenseRetriever, DenseSearchResult

from .openrouter import OpenRouterGenerationClient
from .prompts import build_grounded_prompt


@dataclass(frozen=True)
class BasicRAGResponse:
    answer: str
    source_email_ids: list[str]
    retrieved: list[DenseSearchResult]
    prompt: str


class BasicDenseRAG:
    """Compose independently testable dense retrieval and generation components."""

    def __init__(self, retriever: DenseRetriever, generator: OpenRouterGenerationClient):
        self.retriever = retriever
        self.generator = generator

    def answer(self, question: str, *, top_k: int | None = None) -> BasicRAGResponse:
        retrieved = self.retriever.retrieve(question, top_k=top_k)
        prompt = build_grounded_prompt(question, retrieved)
        answer = self.generator.generate(prompt)
        return BasicRAGResponse(
            answer=answer,
            source_email_ids=[result.email_id for result in retrieved],
            retrieved=retrieved,
            prompt=prompt,
        )
