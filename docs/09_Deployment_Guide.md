# Aegis — "Multi-Agent AI Incident Response Platform"
## Deployment Guide

## Purpose

Instructions for deploying the platform locally, with Docker, and considerations for production deployment.

## Source Traceability

| Component | File |
|---|---|
| Dockerfile | `Dockerfile` |
| Docker Compose | `docker-compose.yml` |
| Prometheus config | `config/prometheus.yml` |
| Environment template | `.env.example` |
| API entry point | `src/main.py` |
| Dashboard entry point | `src/dashboard/app.py` |

## Prerequisites

- Python 3.12+
- Docker & Docker Compose (for full stack)
- OpenRouter API key (or alternative LLM provider)

## Local Development

### 1. Install Dependencies

```bash
pip install pytest fastapi pydantic pydantic-settings httpx \
    langchain-core langchain-openai langgraph openai structlog \
    sqlalchemy aiohttp streamlit
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

### 3. Run Tests

```bash
python -m pytest tests/ -v
```

### 4. Start API Server

```bash
python -m src.main
```

The API starts at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### 5. Start Dashboard

```bash
streamlit run src/dashboard/app.py
```

The dashboard starts at `http://localhost:8501`.

## Docker Deployment

### Full Stack (Docker Compose)

```bash
cp .env.example .env
docker-compose up -d
```

This starts the following services:

| Service | Port | Purpose |
|---|---|---|
| API | 8000 | FastAPI backend |
| Dashboard | 8501 | Streamlit UI |
| PostgreSQL | 5432 | Database + pgvector |
| Redis | 6379 | Cache |
| ChromaDB | 8100 | Vector database |
| Prometheus | 9090 | Metrics collection |
| Grafana | 3000 | Metrics visualization |

### Build Individual Services

```bash
# Build API image
docker build -t agentic-platform .

# Run API only
docker run -p 8000:8000 --env-file .env agentic-platform
```

## Service Dependencies

```
API depends on:
  ├── PostgreSQL (health check required)
  └── Redis (health check required)

Dashboard depends on:
  └── API (health check required)

Prometheus scrapes:
  └── API at /metrics
```

## Configuration Files

### Dockerfile (`Dockerfile`)

- Base: `python:3.11-slim`
- System deps: `gcc`, `libpq-dev`, `curl`
- Python deps: FastAPI, LangChain, LangGraph, SQLAlchemy, asyncpg, Redis, Structlog, OpenAI, pgvector, Streamlit
- Healthcheck: `curl -f http://localhost:8000/health`
- Entrypoint: `python -m src.main`

### Docker Compose (`docker-compose.yml`)

- 7 services with health checks
- Named volumes for data persistence (pgdata, redisdata, chromadata, grafanadata)
- Environment variables from `.env` file
- CORS and networking configured for inter-service communication

## Production Considerations

### Not Yet Implemented

The following are required for production deployment but not yet implemented:

| Requirement | Current State | Required Action |
|---|---|---|
| **Authentication** | JWT config exists, no middleware | Wire in JWT or API key middleware |
| **TLS/SSL** | Not configured | Add reverse proxy (nginx, Traefik) |
| **Secrets management** | `.env` file with defaults | Use vault or K8s secrets |
| **Persistent database** | Engine configured, but incident store is in-memory | Wire incident store to PostgreSQL |
| **Horizontal scaling** | Not possible (in-memory state) | Replace global state with distributed store |
| **CI/CD** | Not configured | Add GitHub Actions pipeline |
| **Health checks** | API health endpoint exists | Add dependency health probes |
| **Rate limiting** | Config exists, not wired | Add middleware |
| **Kubernetes manifests** | Not present | Create Deployment, Service, Ingress YAML |
| **Log aggregation** | Structlog configured | Add log shipping (Filebeat, Fluentd) |

### Recommended Production Architecture

```
Load Balancer
     │
     ├── API Instance 1 (with PostgreSQL, Redis)
     ├── API Instance 2
     └── API Instance N
     
     PostgreSQL (Primary + Replica)
     Redis Cluster
     ChromaDB / pgvector
     Prometheus + Grafana
```

## Monitoring Stack

- **Prometheus:** Configured in `config/prometheus.yml` — scrapes API at `/metrics` every 10s
- **Grafana:** Defined in docker-compose (port 3000), configured to use Prometheus as datasource
- **OpenTelemetry:** Configurable via `MONITORING_OTEL_*` env vars (exporter, endpoint, sample rate)
