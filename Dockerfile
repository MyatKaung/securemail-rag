FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    HF_HOME=/home/securemail/.cache/huggingface \
    HF_HUB_DISABLE_TELEMETRY=1 \
    PYTHONPATH=/app/src \
    PATH=/app/.venv/bin:$PATH

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.11.15 /uv /uvx /bin/

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY src ./src
COPY config ./config
COPY data/sample ./data/sample
COPY .env.example ./

RUN useradd --create-home --uid 10001 securemail \
    && mkdir -p /app/data/monitoring /home/securemail/.cache/huggingface \
    && chown -R securemail:securemail /app /home/securemail

USER securemail
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"

CMD ["uvicorn", "securemail.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
