"""Reproducible acquisition, subset selection, deduplication, and output."""

from __future__ import annotations

import json
import tarfile
from collections.abc import Iterator
from pathlib import Path
from typing import BinaryIO
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .models import NormalizedEmail
from .parser import normalize_message

DEFAULT_DATASET_URL = "https://www.cs.cmu.edu/~enron/enron_mail_20150507.tar.gz"
DEFAULT_DEV_LIMIT = 25
USER_AGENT = "securemail-rag/phase-01-ingestion"


def _is_url(source: str) -> bool:
    return urlparse(source).scheme in {"http", "https"}


def _archive_members(stream: BinaryIO, streaming: bool) -> Iterator[tuple[str, bytes]]:
    mode = "r|gz" if streaming else "r:gz"
    with tarfile.open(fileobj=stream, mode=mode) as archive:
        for member in archive:
            if not member.isfile() or not member.name.startswith("maildir/"):
                continue
            extracted = archive.extractfile(member)
            if extracted is None:
                continue
            yield member.name, extracted.read()


def iter_source_messages(source: str | Path) -> Iterator[tuple[str, bytes]]:
    """Yield source path and raw bytes from a URL, tarball, or maildir directory."""

    source_value = str(source)
    if _is_url(source_value):
        request = Request(source_value, headers={"User-Agent": USER_AGENT})
        with urlopen(request, timeout=120) as response:
            yield from _archive_members(response, streaming=True)
        return

    source_path = Path(source)
    if source_path.is_dir():
        root = source_path.parent if source_path.name == "maildir" else source_path
        for path in sorted(path for path in source_path.rglob("*") if path.is_file()):
            relative = path.relative_to(root).as_posix()
            yield relative, path.read_bytes()
        return

    with source_path.open("rb") as stream:
        yield from _archive_members(stream, streaming=False)


def deduplicate_emails(records: list[NormalizedEmail]) -> list[NormalizedEmail]:
    """Remove duplicate stable IDs and choose the lexicographically first path."""

    selected: dict[str, NormalizedEmail] = {}
    for record in sorted(records, key=lambda item: (item.email_id, item.source_path)):
        selected.setdefault(record.email_id, record)
    return sorted(selected.values(), key=lambda item: item.source_path)


def normalize_source(source: str | Path, limit: int = DEFAULT_DEV_LIMIT) -> list[NormalizedEmail]:
    """Normalize the first ``limit`` unique source messages deterministically."""

    if limit <= 0:
        raise ValueError("limit must be greater than zero")

    records_by_id: dict[str, NormalizedEmail] = {}
    for source_path, raw_bytes in iter_source_messages(source):
        record = normalize_message(raw_bytes, source_path)
        existing = records_by_id.get(record.email_id)
        if existing is None or record.source_path < existing.source_path:
            records_by_id[record.email_id] = record
        if len(records_by_id) >= limit:
            break
    return deduplicate_emails(list(records_by_id.values()))[:limit]


def write_jsonl(records: list[NormalizedEmail], output_path: str | Path) -> None:
    """Write normalized records as deterministic, one-record-per-line JSON."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(
                json.dumps(
                    record.model_dump(mode="json"),
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n"
            )


def download_archive(url: str, destination: str | Path) -> Path:
    """Download the complete public archive atomically for offline processing."""

    destination_path = Path(destination)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = destination_path.with_suffix(destination_path.suffix + ".part")
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=120) as response, temporary_path.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
        temporary_path.replace(destination_path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
    return destination_path
