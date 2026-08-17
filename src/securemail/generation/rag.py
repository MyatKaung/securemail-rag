"""Basic question-to-dense-retrieval-to-grounded-generation flow."""

from __future__ import annotations

from dataclasses import dataclass

from securemail.retrieval import DenseSearchResult, Retriever
from securemail.security import AuthorizationFilter

from .openrouter import OpenRouterGenerationClient
from .prompts import build_grounded_prompt
from .responses import NO_AUTHORIZED_EVIDENCE_MESSAGE


@dataclass(frozen=True)
class BasicRAGResponse:
    answer: str
    source_email_ids: list[str]
    retrieved: list[DenseSearchResult]
    prompt: str


class BasicDenseRAG:
    """Compose independently testable dense retrieval and generation components."""

    def __init__(
        self,
        retriever: Retriever,
        generator: OpenRouterGenerationClient,
        authorization_filter: AuthorizationFilter | None = None,
    ):
        self.retriever = retriever
        self.generator = generator
        self.authorization_filter = authorization_filter
        if authorization_filter is not None:
            setter = getattr(retriever, "set_authorization_filter", None)
            if setter is None:
                raise TypeError("retriever must support pre-retrieval authorization")
            setter(authorization_filter)

    def answer(self, question: str, *, top_k: int | None = None) -> BasicRAGResponse:
        retrieved = self.retriever.retrieve(question, top_k=top_k)
        if self.authorization_filter is not None:
            self.authorization_filter.assert_allowed([result.document for result in retrieved])
        if not retrieved:
            return BasicRAGResponse(
                answer=NO_AUTHORIZED_EVIDENCE_MESSAGE,
                source_email_ids=[],
                retrieved=[],
                prompt="",
            )
        prompt = build_grounded_prompt(
            question,
            retrieved,
            authorization_filter=self.authorization_filter,
        )
        answer = self.generator.generate(prompt)
        return BasicRAGResponse(
            answer=answer,
            source_email_ids=[result.email_id for result in retrieved],
            retrieved=retrieved,
            prompt=prompt,
        )
