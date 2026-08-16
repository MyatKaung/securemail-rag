"""Generation and basic grounded RAG public API."""

from .openrouter import OpenRouterGenerationClient
from .prompts import GROUNDED_SYSTEM_PROMPT, build_grounded_prompt
from .rag import BasicDenseRAG, BasicRAGResponse

__all__ = [
    "GROUNDED_SYSTEM_PROMPT",
    "BasicDenseRAG",
    "BasicRAGResponse",
    "OpenRouterGenerationClient",
    "build_grounded_prompt",
]
