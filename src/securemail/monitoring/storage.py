"""SQLite telemetry and feedback storage behind a replaceable interface."""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from math import ceil
from pathlib import Path
from typing import Any, Protocol

from securemail.config import PROJECT_ROOT

DEFAULT_DB_PATH = PROJECT_ROOT / "data/monitoring/securemail.sqlite3"


@dataclass(frozen=True)
class RequestTelemetry:
    request_id: str
    started_at: str
    total_latency_ms: float
    retrieval_latency_ms: float
    reranking_latency_ms: float
    llm_latency_ms: float
    permission_denied: bool
    refused: bool
    insufficient_evidence: bool
    status_code: int


@dataclass(frozen=True)
class FeedbackRecord:
    request_id: str
    positive: bool
    comment: str | None = None
    created_at: str | None = None


class MonitoringStore(Protocol):
    def record_request(self, telemetry: RequestTelemetry) -> None:
        """Persist one request's aggregate telemetry."""

    def record_feedback(self, feedback: FeedbackRecord) -> bool:
        """Persist feedback if the referenced request exists."""

    def dashboard_metrics(self) -> dict[str, Any]:
        """Return safe aggregated metrics only."""


class SQLiteMonitoringStore:
    """Local SQLite store with no raw question, prompt, or email-content columns."""

    def __init__(self, path: str | Path = DEFAULT_DB_PATH) -> None:
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS request_telemetry (
                    request_id TEXT PRIMARY KEY,
                    started_at TEXT NOT NULL,
                    total_latency_ms REAL NOT NULL,
                    retrieval_latency_ms REAL NOT NULL,
                    reranking_latency_ms REAL NOT NULL,
                    llm_latency_ms REAL NOT NULL,
                    permission_denied INTEGER NOT NULL,
                    refused INTEGER NOT NULL,
                    insufficient_evidence INTEGER NOT NULL,
                    status_code INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT NOT NULL,
                    positive INTEGER NOT NULL,
                    comment TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(request_id) REFERENCES request_telemetry(request_id)
                );
                CREATE INDEX IF NOT EXISTS idx_request_started_at
                    ON request_telemetry(started_at);
                CREATE INDEX IF NOT EXISTS idx_feedback_request_id
                    ON feedback(request_id);
                """
            )

    def record_request(self, telemetry: RequestTelemetry) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO request_telemetry (
                    request_id, started_at, total_latency_ms, retrieval_latency_ms,
                    reranking_latency_ms, llm_latency_ms, permission_denied, refused,
                    insufficient_evidence, status_code
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    telemetry.request_id,
                    telemetry.started_at,
                    telemetry.total_latency_ms,
                    telemetry.retrieval_latency_ms,
                    telemetry.reranking_latency_ms,
                    telemetry.llm_latency_ms,
                    int(telemetry.permission_denied),
                    int(telemetry.refused),
                    int(telemetry.insufficient_evidence),
                    telemetry.status_code,
                ),
            )

    def record_feedback(self, feedback: FeedbackRecord) -> bool:
        created_at = feedback.created_at or datetime.now(UTC).isoformat()
        with self._connect() as connection:
            exists = connection.execute(
                "SELECT 1 FROM request_telemetry WHERE request_id = ?",
                (feedback.request_id,),
            ).fetchone()
            if exists is None:
                return False
            connection.execute(
                """
                INSERT INTO feedback (request_id, positive, comment, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (feedback.request_id, int(feedback.positive), feedback.comment, created_at),
            )
        return True

    @staticmethod
    def _p95(values: Sequence[float]) -> float:
        if not values:
            return 0.0
        ordered = sorted(float(value) for value in values)
        return ordered[max(0, ceil(len(ordered) * 0.95) - 1)]

    def dashboard_metrics(self) -> dict[str, Any]:
        with self._connect() as connection:
            requests = connection.execute(
                """
                SELECT started_at, total_latency_ms, retrieval_latency_ms,
                       reranking_latency_ms, llm_latency_ms, permission_denied,
                       refused, insufficient_evidence
                FROM request_telemetry ORDER BY started_at
                """
            ).fetchall()
            feedback = connection.execute(
                "SELECT positive, COUNT(*) AS count FROM feedback GROUP BY positive"
            ).fetchall()

        total = len(requests)
        total_latencies = [row["total_latency_ms"] for row in requests]
        retrieval_latencies = [row["retrieval_latency_ms"] for row in requests]
        reranking_latencies = [row["reranking_latency_ms"] for row in requests]
        llm_latencies = [row["llm_latency_ms"] for row in requests]
        positive = sum(int(row["count"]) for row in feedback if row["positive"])
        negative = sum(int(row["count"]) for row in feedback if not row["positive"])
        refusal_count = sum(int(row["refused"] or row["insufficient_evidence"]) for row in requests)
        permission_denials = sum(int(row["permission_denied"]) for row in requests)
        requests_by_day: dict[str, int] = {}
        for row in requests:
            day = str(row["started_at"])[:10]
            requests_by_day[day] = requests_by_day.get(day, 0) + 1

        return {
            "total_requests": total,
            "average_end_to_end_latency_ms": sum(total_latencies) / total if total else 0.0,
            "p95_end_to_end_latency_ms": self._p95(total_latencies),
            "average_retrieval_latency_ms": sum(retrieval_latencies) / total if total else 0.0,
            "average_reranking_latency_ms": sum(reranking_latencies) / total if total else 0.0,
            "average_llm_latency_ms": sum(llm_latencies) / total if total else 0.0,
            "permission_denials": permission_denials,
            "refusal_or_insufficient_rate": refusal_count / total if total else 0.0,
            "positive_feedback": positive,
            "negative_feedback": negative,
            "requests_by_day": [
                {"date": date, "count": count} for date, count in sorted(requests_by_day.items())
            ],
        }
