"""Generation and basic grounded RAG public API."""

from .openrouter import (
    OpenRouterGenerationClient,
    OpenRouterGenerationConfig,
    load_generation_config,
)
from .pipeline import GroundedGenerationResult, PermissionAwareGenerationPipeline
from .prompts import GROUNDED_SYSTEM_PROMPT, build_evidence_text, build_grounded_prompt
from .rag import BasicDenseRAG, BasicRAGResponse
from .responses import (
    NO_AUTHORIZED_EVIDENCE_MESSAGE,
    ParsedGeneration,
    parse_basic_response,
    parse_source_email_ids,
    parse_structured_response,
)
from .strategies import (
    BASIC_GROUNDED_STRATEGY,
    BASIC_GROUNDED_V1,
    STRUCTURED_GROUNDED_STRATEGY,
    STRUCTURED_GROUNDED_V1,
    PromptStrategy,
    get_prompt_strategy,
)

__all__ = [
    "BASIC_GROUNDED_STRATEGY",
    "BASIC_GROUNDED_V1",
    "GROUNDED_SYSTEM_PROMPT",
    "NO_AUTHORIZED_EVIDENCE_MESSAGE",
    "STRUCTURED_GROUNDED_STRATEGY",
    "STRUCTURED_GROUNDED_V1",
    "BasicDenseRAG",
    "BasicRAGResponse",
    "GroundedGenerationResult",
    "OpenRouterGenerationClient",
    "OpenRouterGenerationConfig",
    "ParsedGeneration",
    "PermissionAwareGenerationPipeline",
    "PromptStrategy",
    "build_evidence_text",
    "build_grounded_prompt",
    "get_prompt_strategy",
    "load_generation_config",
    "parse_basic_response",
    "parse_source_email_ids",
    "parse_structured_response",
]
