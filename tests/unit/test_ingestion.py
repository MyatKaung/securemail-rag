from securemail.ingestion import (
    NormalizedEmail,
    assign_synthetic_rbac,
    deduplicate_emails,
    normalize_message,
)

RAW_MESSAGE = b"""Message-ID: <ABC-123@example.com>\nDate: Mon, 01 Jan 2001 10:00:00 -0500\nFrom: Alice Example <Alice@Example.com>\nTo: Bob <Bob@Example.com>, carol@example.com\nCc: Dave <DAVE@example.com>\nSubject: Project update\nContent-Type: text/plain; charset=utf-8\n\nHello team.\n\nThe project is on schedule.\n"""


def test_normalize_message_maps_headers_body_and_mailbox():
    record = normalize_message(RAW_MESSAGE, "maildir/finance/ sent/001")

    assert record.message_id == "<abc-123@example.com>"
    assert record.sender == "alice@example.com"
    assert record.recipients_to == ["bob@example.com", "carol@example.com"]
    assert record.recipients_cc == ["dave@example.com"]
    assert record.recipients_bcc == []
    assert record.sent_at == "2001-01-01T15:00:00Z"
    assert record.subject == "Project update"
    assert record.body == "Hello team.\n\nThe project is on schedule."
    assert record.mailbox == "finance"
    assert record.source_path == "maildir/finance/ sent/001"
    assert record.synthetic_role == "finance"


def test_stable_id_does_not_depend_on_source_path():
    first = normalize_message(RAW_MESSAGE, "maildir/alice/inbox/001")
    second = normalize_message(RAW_MESSAGE, "maildir/alice/sent/999")

    assert first.email_id == second.email_id


def test_deduplicate_emails_keeps_lexicographically_first_source_path():
    first = normalize_message(RAW_MESSAGE, "maildir/alice/z-copy")
    second = normalize_message(RAW_MESSAGE, "maildir/alice/a-original")

    result = deduplicate_emails([first, second])

    assert len(result) == 1
    assert result[0].source_path == "maildir/alice/a-original"


def test_malformed_message_is_safe_and_still_normalized():
    malformed = b"From: not an address\nDate: definitely not a date\n\nbody\xff\n"

    record = normalize_message(malformed, "maildir/unknown/inbox/broken")

    assert isinstance(record, NormalizedEmail)
    assert record.email_id.startswith("enron-")
    assert record.sent_at is None
    assert record.subject == ""
    assert record.body == "body\ufffd"
    assert record.sender == "not an address"
    assert record.recipients_to == []


def test_missing_fields_receive_safe_defaults():
    record = normalize_message(b"Subject: only subject\n\n", "maildir/general/inbox/1")

    assert record.sender == ""
    assert record.recipients_to == []
    assert record.sent_at is None
    assert record.subject == "only subject"
    assert record.body == ""


def test_synthetic_rbac_assignment_is_deterministic_and_documented_as_overlay():
    first = assign_synthetic_rbac("legal")
    second = assign_synthetic_rbac("legal")
    unknown = assign_synthetic_rbac("employee-x")

    assert first == second
    assert first.synthetic_role == "legal"
    assert first.department == "legal"
    assert first.access_level == "department"
    assert first.resource_scope == "legal"
    assert unknown.synthetic_role in {"general", "finance", "legal", "executive", "admin"}
