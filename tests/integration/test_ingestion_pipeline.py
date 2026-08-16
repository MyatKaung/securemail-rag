import json
from pathlib import Path

from securemail.ingestion import NormalizedEmail, normalize_source, write_jsonl

MESSAGE = b"""Message-ID: <integration-001@example.com>\nDate: Tue, 02 Jan 2001 12:00:00 +0000\nFrom: sender@example.com\nTo: receiver@example.com\nSubject: Integration sample\n\nA sample message for the ingestion pipeline.\n"""


def test_small_maildir_is_normalized_deduplicated_and_written_end_to_end(tmp_path: Path):
    maildir = tmp_path / "maildir"
    (maildir / "alice-l" / "inbox").mkdir(parents=True)
    (maildir / "alice-l" / "sent").mkdir(parents=True)
    (maildir / "alice-l" / "inbox" / "1").write_bytes(MESSAGE)
    (maildir / "alice-l" / "sent" / "2").write_bytes(MESSAGE)

    records = normalize_source(maildir, limit=10)
    output = tmp_path / "processed" / "dev.jsonl"
    write_jsonl(records, output)

    lines = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 1
    assert len(lines) == 1
    assert lines[0]["mailbox"] == "alice-l"
    assert lines[0]["synthetic_role"] in {
        "general",
        "finance",
        "legal",
        "executive",
        "admin",
    }
    assert lines[0]["email_id"] == records[0].email_id


def test_checked_in_development_sample_has_25_valid_records():
    sample_path = Path(__file__).resolve().parents[2] / "data/sample/enron_dev.sample.jsonl"
    rows = [json.loads(line) for line in sample_path.read_text(encoding="utf-8").splitlines()]

    records = [NormalizedEmail.model_validate(row) for row in rows]

    assert len(records) == 25
    assert len({record.email_id for record in records}) == 25
