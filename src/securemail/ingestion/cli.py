"""Command-line acquisition and normalization entry point."""

from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import (
    DEFAULT_DATASET_URL,
    DEFAULT_DEV_LIMIT,
    download_archive,
    normalize_source,
    write_jsonl,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Acquire and normalize a small Enron subset")
    parser.add_argument(
        "--source",
        default=DEFAULT_DATASET_URL,
        help="public archive URL, local .tar.gz archive, or local maildir directory",
    )
    parser.add_argument("--limit", type=int, default=DEFAULT_DEV_LIMIT)
    parser.add_argument("--output", type=Path, default=Path("data/processed/dev.jsonl"))
    parser.add_argument(
        "--download-archive",
        type=Path,
        help="download the complete source archive to this path and exit",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.download_archive:
        path = download_archive(args.source, args.download_archive)
        print(f"Downloaded archive to {path}")
        return
    records = normalize_source(args.source, limit=args.limit)
    write_jsonl(records, args.output)
    print(f"Wrote {len(records)} normalized emails to {args.output}")


if __name__ == "__main__":
    main()
