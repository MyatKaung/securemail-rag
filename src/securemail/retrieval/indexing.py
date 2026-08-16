"""Load normalized JSONL, prepare documents, embed, and build a dense index."""

from __future__ import annotations

import json
from pathlib import Path

from securemail.ingestion import NormalizedEmail

from .documents import prepare_documents
from .embeddings import Embedder
from .index import DenseIndex


def load_normalized_jsonl(path: str | Path, limit: int | None = None) -> list[NormalizedEmail]:
    """Load normalized records while preserving their stable email IDs."""

    records: list[NormalizedEmail] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            records.append(NormalizedEmail.model_validate(json.loads(line)))
            if limit is not None and len(records) >= limit:
                break
    return records


def build_dense_index(
    normalized_path: str | Path,
    embedder: Embedder,
    *,
    limit: int | None = None,
    max_chars: int = 12_000,
) -> DenseIndex:
    """Prepare normalized emails and build the dense vector index."""

    emails = load_normalized_jsonl(normalized_path, limit=limit)
    documents = prepare_documents(emails, max_chars=max_chars)
    vectors = embedder.embed([document.text for document in documents])
    return DenseIndex.build(documents, vectors)
