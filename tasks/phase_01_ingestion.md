# Phase 01 — Enron Ingestion

## Goal
Acquire/parse a documented Enron subset and normalize it reproducibly.

## Tasks
- [x] Implement dataset acquisition instructions/script.
- [x] Normalize sender/recipients/date/subject/body/mailbox.
- [x] Create stable email IDs.
- [x] Deduplicate.
- [x] Apply documented synthetic RBAC metadata.
- [x] Create dev/eval subset selection.
- [x] Add ingestion tests.

## Phase 01 verification

- Source: CMU May 7, 2015 release at `https://www.cs.cmu.edu/~enron/enron_mail_20150507.tar.gz`.
- Development subset: 25 unique normalized emails in `data/sample/enron_dev.sample.jsonl`.
- `uv run make lint` passes.
- `uv run make test-ci` passes: 17 tests.
- The full archive is never written to the repository; the default path streams only the configured subset.
