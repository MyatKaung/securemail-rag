"""FastAPI application boundary for secure end-to-end RAG queries."""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from securemail import __version__
from securemail.config import ConfigurationError
from securemail.security import AuthorizationError

from .schemas import QueryRequest, QueryResponse
from .service import (
    MalformedPrincipalError,
    QueryService,
    QueryServiceError,
    build_default_service,
)
from .ui import render_ui


def create_app(service: QueryService | None = None) -> FastAPI:
    app = FastAPI(title="SecureMail RAG", version=__version__)
    resolved_service = service

    def get_service() -> QueryService:
        nonlocal resolved_service
        if resolved_service is None:
            resolved_service = build_default_service()
        return resolved_service

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

    return app


app = create_app()
