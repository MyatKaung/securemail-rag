"""FastAPI application boundary for secure end-to-end RAG queries."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
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
from securemail.security import (
    DEMO_IDENTITIES,
    SESSION_COOKIE_NAME,
    AuthorizationError,
    DemoAuthenticator,
    DemoIdentity,
    DemoSessionManager,
    InvalidDemoCredentialsError,
)

from .schemas import (
    FeedbackRequest,
    FeedbackResponse,
    LoginRequest,
    LoginResponse,
    QueryRequest,
    QueryResponse,
)
from .service import (
    MalformedPrincipalError,
    QueryService,
    QueryServiceError,
    build_default_service,
    validate_runtime_assets,
)
from .ui import render_login, render_ui


def create_app(
    service: QueryService | None = None,
    monitoring_store: MonitoringStore | None = None,
    demo_authenticator: DemoAuthenticator | None = None,
    session_secret: str | None = None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        validate_runtime_assets()
        yield

    app = FastAPI(title="SecureMail RAG", version=__version__, lifespan=lifespan)
    resolved_service = service
    app_monitoring_store = monitoring_store or SQLiteMonitoringStore()
    authenticator = demo_authenticator or DemoAuthenticator.from_config()
    session_manager = DemoSessionManager(session_secret)
    configure_structured_logging()

    def get_service() -> QueryService:
        nonlocal resolved_service
        if resolved_service is None:
            resolved_service = build_default_service()
        return resolved_service

    def get_monitoring_store() -> MonitoringStore:
        service_store = getattr(resolved_service, "monitoring_store", None)
        return service_store or app_monitoring_store

    def current_identity(request: Request) -> DemoIdentity | None:
        email = session_manager.resolve_email(request.cookies.get(SESSION_COOKIE_NAME))
        return DEMO_IDENTITIES.get(email) if email is not None else None

    def require_identity(request: Request) -> DemoIdentity:
        identity = current_identity(request)
        if identity is None:
            raise HTTPException(status_code=401, detail="login required")
        return identity

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

    @app.get("/login", response_class=HTMLResponse, include_in_schema=False)
    def login_page() -> str:
        return render_login()

    @app.post("/login", response_model=LoginResponse, tags=["auth"])
    def login(request: LoginRequest, response: Response) -> LoginResponse:
        try:
            identity = authenticator.authenticate(request.email, request.password)
        except InvalidDemoCredentialsError as exc:
            raise HTTPException(status_code=401, detail="invalid demo credentials") from exc
        session_manager.set_cookie(response, identity.email)
        return LoginResponse(
            email=identity.email,
            department=identity.principal.department,
            role=identity.principal.role,
        )

    @app.get("/logout", tags=["auth"])
    def logout() -> RedirectResponse:
        response = RedirectResponse(url="/login", status_code=303)
        session_manager.clear_cookie(response)
        return response

    @app.get("/", response_class=HTMLResponse, response_model=None, include_in_schema=False)
    def ui(request: Request) -> str | RedirectResponse:
        identity = current_identity(request)
        if identity is None:
            return RedirectResponse(url="/login", status_code=303)
        return render_ui(identity)

    @app.post("/query", response_model=QueryResponse, tags=["rag"])
    def query(request: Request, payload: QueryRequest) -> QueryResponse:
        try:
            identity = require_identity(request)
            return get_service().query(payload, identity_email=identity.email)
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
