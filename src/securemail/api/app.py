"""FastAPI application boundary for secure end-to-end RAG queries."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from securemail import __version__
from securemail.config import ConfigurationError
from securemail.monitoring import (
    FeedbackRecord,
    MonitoringStore,
    SQLiteMonitoringStore,
    new_request_id,
    reset_request_id,
    set_request_id,
    valid_request_id,
)
from securemail.monitoring.dashboard import render_dashboard
from securemail.monitoring.logging import configure_structured_logging, log_event
from securemail.security import AuthorizationError

from .schemas import FeedbackRequest, FeedbackResponse, QueryRequest, QueryResponse
from .service import (
    MalformedPrincipalError,
    QueryService,
    QueryServiceError,
    build_default_service,
)
from .ui import render_ui


def create_app(
    service: QueryService | None = None,
    monitoring_store: MonitoringStore | None = None,
) -> FastAPI:
    app = FastAPI(title="SecureMail RAG", version=__version__)
    resolved_service = service
    app_monitoring_store = monitoring_store or SQLiteMonitoringStore()
    configure_structured_logging()

    def get_service() -> QueryService:
        nonlocal resolved_service
        if resolved_service is None:
            resolved_service = build_default_service()
        return resolved_service

    def get_monitoring_store() -> MonitoringStore:
        service_store = getattr(resolved_service, "monitoring_store", None)
        return service_store or app_monitoring_store

    @app.middleware("http")
    async def correlation_middleware(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        supplied_id = request.headers.get("X-Request-ID", "")
        request_id = supplied_id if valid_request_id(supplied_id) else new_request_id()
        token = set_request_id(request_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            reset_request_id(token)

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def ui() -> str:
        return render_ui()

    @app.post("/query", response_model=QueryResponse, tags=["rag"])
    def query(request: QueryRequest) -> QueryResponse:
        try:
            return get_service().query(request)
        except MalformedPrincipalError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except ConfigurationError as exc:
            raise HTTPException(
                status_code=503,
                detail=f"OpenRouter generation is unavailable: {exc}",
            ) from exc
        except AuthorizationError as exc:
            raise HTTPException(status_code=403, detail="authorization denied") from exc
        except QueryServiceError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @app.post("/feedback", response_model=FeedbackResponse, tags=["monitoring"])
    def feedback(request: FeedbackRequest) -> FeedbackResponse:
        try:
            recorded = get_monitoring_store().record_feedback(
                FeedbackRecord(
                    request_id=request.request_id,
                    positive=request.positive,
                    comment=request.comment,
                )
            )
        except Exception as exc:
            log_event("feedback_write_failed", error_type=type(exc).__name__)
            raise HTTPException(status_code=503, detail="feedback storage unavailable") from exc
        if not recorded:
            raise HTTPException(status_code=404, detail="request ID was not found")
        log_event("feedback_recorded", positive=request.positive)
        return FeedbackResponse(request_id=request.request_id, recorded=True)

    @app.get("/monitoring/metrics", tags=["monitoring"])
    def monitoring_metrics() -> dict[str, object]:
        try:
            return get_monitoring_store().dashboard_metrics()
        except Exception as exc:
            log_event("monitoring_read_failed", error_type=type(exc).__name__)
            raise HTTPException(status_code=503, detail="monitoring storage unavailable") from exc

    @app.get("/monitoring", response_class=HTMLResponse, include_in_schema=False)
    def monitoring_page() -> str:
        return render_dashboard()

    return app


app = create_app()
