FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Python deps (install from lock / requirements first for layer caching)
COPY pyproject.toml ./
RUN pip install --upgrade pip && \
    pip install fastapi uvicorn pydantic pydantic-settings \
    langchain-core langchain-openai langgraph \
    sqlalchemy[asyncio] asyncpg \
    redis structlog \
    openai pgvector streamlit

COPY src/ src/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "src.main"]
