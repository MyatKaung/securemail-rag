"""Timing decorators that preserve existing retrieval and generation interfaces."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any

from .logging import log_event


@dataclass
class PhaseTimings:
    retrieval_latency_ms: float = 0.0
    reranking_latency_ms: float = 0.0
    llm_latency_ms: float = 0.0


class TimedRetriever:
    def __init__(self, retriever: Any, timings: PhaseTimings) -> None:
        self.retriever = retriever
        self.timings = timings

    def set_authorization_filter(self, authorization_filter: Any) -> None:
        self.retriever.set_authorization_filter(authorization_filter)

    def retrieve(self, question: str, top_k: int | None = None) -> list[Any]:
        started = perf_counter()
        try:
            return self.retriever.retrieve(question, top_k=top_k)
        finally:
            elapsed_ms = (perf_counter() - started) * 1000
            self.timings.retrieval_latency_ms += elapsed_ms
            log_event("retrieval_completed", retrieval_latency_ms=round(elapsed_ms, 3))


class TimedReranker:
    def __init__(self, reranker: Any, timings: PhaseTimings) -> None:
        self.reranker = reranker
        self.timings = timings

    def rerank(self, query: str, candidates: list[Any], *, final_k: int) -> list[Any]:
        started = perf_counter()
        try:
            return self.reranker.rerank(query, candidates, final_k=final_k)
        finally:
            elapsed_ms = (perf_counter() - started) * 1000
            self.timings.reranking_latency_ms += elapsed_ms
            log_event("reranking_completed", reranking_latency_ms=round(elapsed_ms, 3))


class TimedGenerationClient:
    def __init__(self, generator: Any, timings: PhaseTimings) -> None:
        self.generator = generator
        self.timings = timings

    def generate(self, prompt: str, *, system_prompt: str, **kwargs: object) -> str:
        started = perf_counter()
        try:
            return self.generator.generate(prompt, system_prompt=system_prompt, **kwargs)
        finally:
            elapsed_ms = (perf_counter() - started) * 1000
            self.timings.llm_latency_ms += elapsed_ms
            log_event("generation_completed", llm_latency_ms=round(elapsed_ms, 3))
