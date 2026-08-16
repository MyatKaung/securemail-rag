"""FastAPI application boundary for the Phase 00 skeleton."""

from fastapi import FastAPI

from securemail import __version__


def create_app() -> FastAPI:
    app = FastAPI(title="SecureMail RAG", version=__version__)

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
