import json
import logging
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient

from securemail.api import create_app
from securemail.api.service import DefaultRAGService
from securemail.monitoring import FeedbackRecord, RequestTelemetry, SQLiteMonitoringStore
from securemail.monitoring.logging import JsonFormatter, configure_structured_logging, log_event
from securemail.retrieval.documents import RetrievalDocument
from securemail.retrieval.index import DenseIndex
from securemail.retrieval.reranking import CrossEncoderReranker


class FakeEmbedder:
    def embed(self, texts: list[str]) -> np.ndarray:
        return np.asarray(
            [
                [float("finance" in text.casefold()), float("legal" in text.casefold())]
                for text in texts
            ],
            dtype=np.float32,
        )


class FakeCrossEncoder:
    def predict(self, pairs: list[tuple[str, str]]) -> list[float]:
        return [float("finance" in document.casefold()) for _, document in pairs]


class FakeGenerator:
    def generate(self, prompt: str, *, system_prompt: str, **kwargs: object) -> str:
        del prompt, system_prompt, kwargs
        return "The finance plan is supported.\nSources: [finance-email]"


def make_service(store: SQLiteMonitoringStore) -> DefaultRAGService:
    documents = [
        RetrievalDocument(
            "finance-email",
            "Subject: finance plan\nBody: Finance evidence.",
            {"department": "finance", "access_level": "department", "resource_scope": "finance"},
        ),
        RetrievalDocument(
            "legal-email",
            "Subject: legal plan\nBody: Restricted legal evidence.",
            {"department": "legal", "access_level": "department", "resource_scope": "legal"},
        ),
    ]
    embedder = FakeEmbedder()
    index = DenseIndex(documents, embedder.embed([document.text for document in documents]))
    return DefaultRAGService(
        index=index,
        embedder=embedder,
        reranker=CrossEncoderReranker(model=FakeCrossEncoder()),
        generator=FakeGenerator(),
        candidate_k=2,
        final_k=2,
        monitoring_store=store,
    )


def payload() -> dict[str, object]:
    return {
        "question": "What is the finance plan?",
        "principal": {
            "role": "employee",
            "department": "finance",
            "access_level": "department",
            "resource_scope": "finance",
        },
    }


def test_telemetry_creation_and_request_id_propagation(tmp_path: Path) -> None:
    store = SQLiteMonitoringStore(tmp_path / "monitoring.sqlite3")
    client = TestClient(create_app(make_service(store), monitoring_store=store))

    response = client.post("/query", json=payload(), headers={"X-Request-ID": "trace-123"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "trace-123"
    assert response.json()["request_id"] == "trace-123"
    metrics = store.dashboard_metrics()
    assert metrics["total_requests"] == 1
    assert metrics["average_retrieval_latency_ms"] >= 0
    assert metrics["average_reranking_latency_ms"] >= 0
    assert metrics["average_llm_latency_ms"] >= 0


def test_feedback_persistence_and_invalid_or_missing_request_id(tmp_path: Path) -> None:
    store = SQLiteMonitoringStore(tmp_path / "monitoring.sqlite3")
    store.record_request(
        RequestTelemetry(
            "known-request", "2026-08-16T00:00:00+00:00", 1, 1, 1, 1, False, False, False, 200
        )
    )
    client = TestClient(create_app(monitoring_store=store))

    accepted = client.post(
        "/feedback",
        json={"request_id": "known-request", "positive": True, "comment": "helpful"},
    )
    unknown = client.post("/feedback", json={"request_id": "missing", "positive": False})
    invalid = client.post("/feedback", json={"request_id": "not valid", "positive": True})

    assert accepted.status_code == 200
    assert accepted.json() == {"request_id": "known-request", "recorded": True}
    assert unknown.status_code == 404
    assert invalid.status_code == 422
    assert store.dashboard_metrics()["positive_feedback"] == 1


def test_permission_denial_metric_and_dashboard_fixture(tmp_path: Path) -> None:
    fixture_path = Path(__file__).parents[1] / "fixtures/monitoring_events.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    store = SQLiteMonitoringStore(tmp_path / "monitoring.sqlite3")
    for row in fixture["requests"]:
        store.record_request(RequestTelemetry(**row))
    for row in fixture["feedback"]:
        assert store.record_feedback(FeedbackRecord(**row))

    metrics = store.dashboard_metrics()
    assert metrics["total_requests"] == 3
    assert metrics["p95_end_to_end_latency_ms"] == 300.0
    assert metrics["permission_denials"] == 1
    assert metrics["refusal_or_insufficient_rate"] == 2 / 3
    assert metrics["positive_feedback"] == 1
    assert metrics["negative_feedback"] == 1
    assert len(metrics["requests_by_day"]) == 2


def test_dashboard_page_is_aggregated_only(tmp_path: Path) -> None:
    store = SQLiteMonitoringStore(tmp_path / "monitoring.sqlite3")
    response = TestClient(create_app(monitoring_store=store)).get("/monitoring")

    assert response.status_code == 200
    assert "Average LLM latency" in response.text
    assert "Permission denials" in response.text
    assert "email bodies" in response.text


def test_query_ui_contains_request_id_feedback_controls() -> None:
    response = TestClient(create_app()).get("/")

    assert response.status_code == 200
    assert 'id="positive"' in response.text
    assert 'id="negative"' in response.text
    assert "lastRequestId" in response.text
    assert "fetch('/feedback'" in response.text


def test_structured_logs_do_not_include_secrets_or_sensitive_fields(caplog) -> None:
    configure_structured_logging(logging.INFO)
    with caplog.at_level(logging.INFO, logger="securemail"):
        log_event(
            "test_event",
            request_id="safe-id",
            api_key="do-not-log",
            question="private question",
            prompt="private prompt",
            body="private email body",
            comment="private comment",
            count=3,
        )

    rendered = JsonFormatter().format(caplog.records[-1])
    assert "do-not-log" not in rendered
    assert "private question" not in rendered
    assert "private prompt" not in rendered
    assert "private email body" not in rendered
    assert "private comment" not in rendered
    assert '"count":3' in rendered
