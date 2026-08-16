# Data Design

## Phase 01 Source and Raw Format

The acquisition path uses the May 7, 2015 Enron Email Dataset release hosted by
Carnegie Mellon University:

`https://www.cs.cmu.edu/~enron/enron_mail_20150507.tar.gz`

The source page is `https://www.cs.cmu.edu/~enron/index.html`. The archive is a
gzip-compressed tar file containing RFC 2822/MIME message files under
`maildir/<mailbox>/<folder>/<message-file>`. The complete archive is not stored
in this repository. Phase 01 streams the archive and takes the first 25 unique
messages by archive order for the checked-in development sample; the limit is
configurable.

## Enron Email Record
The Phase 01 normalized JSONL schema is:
- `email_id`
- `message_id` when available
- `sender`
- `recipients_to`
- `recipients_cc`
- `recipients_bcc`
- `sent_at`
- `subject`
- `body`
- `mailbox`
- `source_path`

Phase 01 also adds the following explicitly synthetic experiment fields:
- `synthetic_role`
- `department`
- `access_level`
- `resource_scope`

Missing sender/recipient/subject values become empty strings or empty lists;
invalid dates become `null`; malformed text is decoded with replacement
characters rather than aborting the pipeline.

`email_id` is a SHA-256-based identifier. When present, the normalized
`Message-ID` is the identity seed; otherwise the normalized sender, recipients,
date, subject, and body are used. Deduplication keeps one record per stable ID
and chooses the lexicographically first `source_path` when duplicates occur.

## Synthetic Authorization Metadata
For controlled evaluation, overlay fields such as:
- `department`
- `access_level`
- `resource_scope`

Example roles:
- general
- finance
- legal
- executive
- admin

Important:
The authorization map is synthetic and must be described as such. Phase 01 does
not reconstruct or claim Enron's historical permissions. The role assignment is
deterministic: explicit mailbox keywords map to matching experiment roles, and
other mailboxes use a SHA-256 bucket. The output policy is versioned as
`synthetic-enron-overlay-v1` in code.

## Dataset Size Strategy
Suggested:
- dev: ~2,000 emails
- eval: ~10,000 emails
- final demo: ~10,000–20,000 if practical

Do not scale before evaluation and correctness are stable.
