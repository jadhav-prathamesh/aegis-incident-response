# Contest Deployment

## Purpose

Document how the platform is deployed and the infrastructure required to run it.

## Source Traceability

| Component | File |
|---|---|
| Container definition | `Dockerfile` |
| Service orchestration | `docker-compose.yml` |
| Environment configuration | `.env.example` |
| Monitoring configuration | `config/prometheus.yml` |
| Application entry point | `src/main.py` |

## Deployment Options

### Option 1: Docker Compose (Full Stack)

**Prerequisites:** Docker & Docker Compose

```bash
cp .env.example .env
# Edit .env with API keys
docker-compose up -d
```

This starts 7 services:

| Service | Image | Port | Purpose |
|---|---|---|---|
| api | Custom build | 8000 | FastAPI backend |
| dashboard | Custom build | 8501 | Streamlit UI |
| postgres | pgvector/pg16 | 5432 | Database + vector store |
| redis | redis:7-alpine | 6379 | Cache |
| chroma | chromadb/chroma | 8100 | Vector database |
| prometheus | prom/prometheus | 9090 | Metrics |
| grafana | grafana/grafana | 3000 | Dashboards |

**Health checks:** All services have health checks configured.

**Volumes:** Named volumes for PostgreSQL data, Redis data, Chroma data, and Grafana data.

### Option 2: Local Development

**Prerequisites:** Python 3.12+

```bash
pip install -r requirements.txt  # or individual deps
cp .env.example .env
python -m src.main               # API at localhost:8000
streamlit run src/dashboard/app.py  # Dashboard at localhost:8501
```

### Option 3: Single Docker Container

```bash
docker build -t agentic-platform .
docker run -p 8000:8000 --env-file .env agentic-platform
```

## Infrastructure Requirements

### Minimum (Local/Docker)
- 4 GB RAM
- 2 CPU cores
- 10 GB disk
- Docker 24+

### Recommended (Development)
- 8 GB RAM
- 4 CPU cores
- 20 GB SSD
- Docker 24+

### Production (Future)
- Requires additional security and scaling measures (see notes)

## Service Dependencies

```
api:  requires postgres (healthy), redis (healthy)
dashboard: requires api (healthy)
prometheus: standalone
grafana: depends on prometheus
```

## Environment Configuration

All configuration is via environment variables (`.env` file). Key groups:

| Group | Variables | Required |
|---|---|---|
| Application | APP_NAME, APP_VERSION, APP_ENV | No (defaults) |
| API | API_HOST, API_PORT, API_WORKERS | No (defaults) |
| Database | DATABASE_URL, DB_POOL_SIZE | No (defaults) |
| LLM | OPENROUTER_API_KEY, LLM_MODEL | **Yes** for full AI |
| Redis | REDIS_URL | No (defaults) |
| Security | JWT_SECRET_KEY | No (not yet wired) |

## Network Configuration

Default ports used by the platform:

| Port | Service | Docker | External |
|---|---|---|---|
| 8000 | API | ✓ | ✓ |
| 8501 | Dashboard | ✓ | ✓ |
| 5432 | PostgreSQL | ✓ | ✓ |
| 6379 | Redis | ✓ | ✓ |
| 8100 | ChromaDB | ✓ | ✓ |
| 9090 | Prometheus | ✓ | ✓ |
| 3000 | Grafana | ✓ | ✓ |

## Production Deployment Gaps

**Important:** The following are required for production deployment but not yet implemented:

| Requirement | Status | Action Required |
|---|---|---|
| Authentication | Configured only (JWT settings exist, no middleware) | Wire FastAPI middleware |
| TLS/SSL | Not configured | Add reverse proxy |
| Secrets management | .env file with placeholders | Use Vault/K8s secrets |
| Persistent incident store | In-memory only | Migrate to PostgreSQL |
| Horizontal scaling | Not possible | Replace global state |
| CI/CD | Not configured | Add GitHub Actions |
| Monitoring dashboards | Grafana configured but no dashboards | Import/create dashboards |
| Backup strategy | Not configured | Add pg_dump / volume snapshots |
