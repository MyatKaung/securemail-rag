"""Enron acquisition and normalization public API."""

from .models import NormalizedEmail
from .parser import mailbox_from_source_path, normalize_message
from .pipeline import (
    DEFAULT_DATASET_URL,
    DEFAULT_DEV_LIMIT,
    deduplicate_emails,
    download_archive,
    iter_source_messages,
    normalize_source,
    write_jsonl,
)
from .rbac import (
    SYNTHETIC_POLICY_VERSION,
    SYNTHETIC_ROLES,
    SyntheticRBACMetadata,
    assign_synthetic_rbac,
)

__all__ = [
    "DEFAULT_DATASET_URL",
    "DEFAULT_DEV_LIMIT",
    "SYNTHETIC_POLICY_VERSION",
    "SYNTHETIC_ROLES",
    "NormalizedEmail",
    "SyntheticRBACMetadata",
    "assign_synthetic_rbac",
    "deduplicate_emails",
    "download_archive",
    "iter_source_messages",
    "mailbox_from_source_path",
    "normalize_message",
    "normalize_source",
    "write_jsonl",
]
