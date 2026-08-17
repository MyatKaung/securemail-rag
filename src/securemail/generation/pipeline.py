"""Permission-aware retrieval-to-generation boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from securemail.retrieval import DenseSearchResult, Retriever
from securemail.security import AuthorizationFilter

from .responses import NO_AUTHORIZED_EVIDENCE_MESSAGE, ParsedGeneration
from .strategies import PromptStrategy


class GenerationClient(Protocol):
    def generate(self, prompt: str, *, system_prompt: str, **kwargs: object) -> str:
        """Generate text without exposing provider credentials to the caller."""


@dataclass(frozen=True)
class GroundedGenerationResult:
    question: str
    strategy_name: str
    prompt_version: str
    prompt: str
    retrieved: list[DenseSearchResult]
    parsed: ParsedGeneration

    @property
    def answer(self) -> str:
        return self.parsed.answer

    @property
    def source_email_ids(self) -> list[str]:
        return self.parsed.source_email_ids


class PermissionAwareGenerationPipeline:
    """Require pre-authorized retrieval and re-check before the LLM call."""

    def __init__(
        self,
        retriever: Retriever,
        generator: GenerationClient,
        authorization_filter: AuthorizationFilter,
        strategy: PromptStrategy,
    ) -> None:
        self.retriever = retriever
        self.generator = generator
        self.authorization_filter = authorization_filter
        self.strategy = strategy
        setter = getattr(retriever, "set_authorization_filter", None)
        if setter is None:
            raise TypeError("retriever must support pre-retrieval authorization")
        setter(authorization_filter)

    def answer(self, question: str, *, top_k: int = 5) -> GroundedGenerationResult:
        retrieved = self.retriever.retrieve(question, top_k=top_k)
        # Fail closed before prompt construction or any provider call.
        self.authorization_filter.assert_allowed([result.document for result in retrieved])
        if not retrieved:
            parsed = ParsedGeneration(
                raw_text=NO_AUTHORIZED_EVIDENCE_MESSAGE,
                answer=NO_AUTHORIZED_EVIDENCE_MESSAGE,
                source_email_ids=[],
                uncertainty=NO_AUTHORIZED_EVIDENCE_MESSAGE,
                refused=False,
            )
            return GroundedGenerationResult(
                question=question,
                strategy_name=self.strategy.name,
                prompt="",
                prompt_version=self.strategy.version,
                retrieved=[],
                parsed=parsed,
            )
        prompt = self.strategy.build_prompt(
            question,
            retrieved,
            authorization_filter=self.authorization_filter,
        )
        raw_response = self.generator.generate(
            prompt,
            system_prompt=self.strategy.system_prompt,
        )
        return GroundedGenerationResult(
            question=question,
            strategy_name=self.strategy.name,
            prompt_version=self.strategy.version,
            prompt=prompt,
            retrieved=retrieved,
            parsed=self.strategy.parse(raw_response),
        )
