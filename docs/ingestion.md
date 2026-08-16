# Phase 01 — Enron Ingestion

## Acquisition source

SecureMail RAG uses the public CMU May 7, 2015 release:

`https://www.cs.cmu.edu/~enron/enron_mail_20150507.tar.gz`

The source is a gzip-compressed tar archive of RFC 2822/MIME messages stored in
a maildir hierarchy. The archive is public research data; it contains historical
Enron email and is not an authorization policy. The project does not commit the
full archive.

## Reproducible commands

Stream a small development subset directly from the public source:

```bash
PYTHONPATH=src uv run --extra dev python -m securemail.ingestion.cli \
  --source https://www.cs.cmu.edu/~enron/enron_mail_20150507.tar.gz \
  --limit 25 \
  --output data/processed/dev.jsonl
```

For offline processing, download the complete archive explicitly, then process
it locally:

```bash
PYTHONPATH=src uv run --extra dev python -m securemail.ingestion.cli \
  --download-archive data/raw/enron_mail_20150507.tar.gz

PYTHONPATH=src uv run --extra dev python -m securemail.ingestion.cli \
  --source data/raw/enron_mail_20150507.tar.gz \
  --limit 25 \
  --output data/processed/dev.jsonl
```

The checked-in `data/sample/enron_dev.sample.jsonl` is a small processed sample
generated from the same public source. It contains normalized data only and no
retrieval ground-truth labels.

## Normalization behavior

Each message is parsed with Python's RFC 2822/MIME email parser. The pipeline
normalizes sender and recipient addresses, decodes subjects, converts valid
dates to UTC ISO-8601 strings, extracts text bodies, derives a stable SHA-256
`email_id`, and records mailbox/source information. Missing or malformed fields
are retained as safe empty/null values. Duplicate stable IDs are collapsed
deterministically.

The RBAC fields are a deterministic synthetic overlay for this experiment only;
they do not represent Enron's historical access controls.
