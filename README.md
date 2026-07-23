# Aegis — "Multi-Agent AI Incident Response Platform"

A multi-agent AI incident response platform for automated production incident management that orchestrates the full incident lifecycle: understanding, root cause analysis, remediation planning, execution, monitoring, and validation.

## Architecture

```
Incident → Orchestrator → Planner → Executor → Observer → Validator
              ↓              ↓           ↓           ↓           ↓
          Decision      RCA Plan    Actions    Health     Validation
                        + Search    + Approval  + Metrics  + Compliance
```

### Core Agents

| Agent | Responsibility |
|-------|---------------|
| **Orchestrator** | Receives incidents, makes LLM-driven decisions, coordinates all agents |
| **Planner** | Incident understanding, task decomposition, remediation planning via vector search |
| **Executor** | Runs approved actions (restart, scale, rollback, failover, etc.) |
| **Observer** | Health checks, Prometheus metrics, alert correlation, log analysis |
| **Validator** | Verifies fixes via synthetic tests, compliance checks, baseline comparison |

### Core Services

| Module | Description |
|--------|-------------|
| `config.py` | Pydantic Settings with 11 nested configuration groups |
| `models.py` | 30+ Pydantic domain models and enums |
| `exceptions.py` | 30+ typed exception classes with HTTP mapping |
| `embeddings.py` | OpenAI-compatible embedding service with local fallback |
| `vector_db.py` | ChromaDB and pgvector backends |
| `knowledge_base.py` | Semantic + lexical hybrid knowledge search |
| `action_dispatcher.py` | 15 action handlers with real shell execution |
| `approval.py` | Full approval workflow with dev auto-approve |
| `monitoring.py` | HTTP/TCP health, Prometheus, Alertmanager, k8s status |
| `validation.py` | Synthetic tests, compliance, baseline comparison |
| `similar_incidents.py` | Vector + brute-force incident similarity search |
| `incident_store.py` | In-memory incident repository |
| `logging.py` | Structlog with stdlib fallback |

## Tech Stack

- **Language:** Python 3.12+
- **AI:** LangGraph, LangChain, OpenAI-compatible APIs
- **Backend:** FastAPI + uvicorn
- **Vector DB:** ChromaDB / pgvector
- **Cache:** Redis
- **Database:** PostgreSQL (asyncpg)
- **Monitoring:** Prometheus, Grafana
- **Dashboard:** Streamlit
- **Infrastructure:** Docker, Docker Compose
- **Testing:** pytest (54 tests)

## Quick Start

### Prerequisites

- Python 3.12+
- Docker & Docker Compose (for full stack)

### Local Development (Windows)

```powershell
# 1. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate

# 2. Install all dependencies
pip install -e ".[dev]"

# 3. Run all tests (54 tests)
python -m pytest tests/ -v

# 4. Start the API server (http://localhost:8000)
python -m src.main

# 5. Start the dashboard (http://localhost:8501)
streamlit run src/dashboard/app.py
```

> **Note on Windows**: If you encounter a `uuid_utils` DLL error, this is caused by Windows Application Control policies blocking the native extension. The application automatically falls back to pure Python UUID generation — no action needed.

### Quick API Verification

```bash
# In another terminal, verify the API is running:
curl http://localhost:8000/health
# Response: {"status":"healthy","version":"1.0.0"}

curl http://localhost:8000/ready
# Response: {"status":"ready"}
```

### Docker Compose (Full Stack)

```bash
# Copy and edit environment config
cp .env.example .env

# Start all services
docker-compose up -d
```

This starts:
- **API** — `http://localhost:8000`
- **Dashboard** — `http://localhost:8501`
- **PostgreSQL** — `localhost:5432`
- **Redis** — `localhost:6379`
- **ChromaDB** — `localhost:8100`
- **Prometheus** — `localhost:9090`
- **Grafana** — `localhost:3000`

## API Endpoints

### Health
- `GET /health` — Liveness probe
- `GET /ready` — Readiness probe
- `GET /info` — Platform info

### Incidents
- `GET /api/v1/incidents` — List all incidents
- `GET /api/v1/incidents/{id}` — Get incident by ID
- `POST /api/v1/incidents` — Create incident
- `PATCH /api/v1/incidents/{id}` — Update incident
- `GET /api/v1/incidents/{id}/similar` — Find similar incidents

### Approvals
- `GET /api/v1/approvals/pending` — List pending approvals
- `POST /api/v1/approvals` — Create approval request
- `POST /api/v1/approvals/{id}/approve` — Approve
- `POST /api/v1/approvals/{id}/reject` — Reject

### Agents
- `POST /api/v1/agents/execute` — Execute agent task
- `GET /api/v1/agents/types` — List agent types
- `GET /api/v1/agents/{type}/health` — Agent health check

### Monitoring
- `GET /api/v1/monitoring/health/{service}` — HTTP health check
- `GET /api/v1/monitoring/metrics/{resource}` — Resource metrics
- `GET /api/v1/monitoring/alerts` — Active alerts
- `GET /api/v1/monitoring/deployments/{service}` — Deployment status

### Validation
- `POST /api/v1/validation/synthetic` — Run synthetic test
- `POST /api/v1/validation/alerts` — Verify alert resolution
- `POST /api/v1/validation/compliance` — Check compliance
- `POST /api/v1/validation/baselines` — Compare baselines
- `POST /api/v1/validation/rollback` — Validate rollback

## Configuration

All configuration is managed via environment variables or `.env` file. Nested settings use prefixed env vars:

| Prefix | Settings Class | Example |
|--------|---------------|---------|
| `DB_` | DatabaseSettings | `DB_HOST=localhost` |
| `REDIS_` | RedisSettings | `REDIS_PORT=6379` |
| `VECTOR_DB_` | VectorDBSettings | `VECTOR_DB_PROVIDER=chroma` |
| `LLM_` | LLMSettings | `LLM_MODEL=gpt-4` |
| `AGENT_` | AgentSettings | `AGENT_DEFAULT_TIMEOUT=300` |
| `SECURITY_` | SecuritySettings | `SECURITY_SECRET_KEY=...` |
| `MONITORING_` | MonitoringSettings | `MONITORING_PROMETHEUS_URL=...` |
| `INTEGRATION_` | IntegrationSettings | `INTEGRATION_SLACK_ENABLED=true` |

## Project Structure

```
incident-intelligence-platform/
├── src/
│   ├── core/           # Domain logic, services, models
│   ├── agents/         # AI agent implementations (LangGraph)
│   ├── api/            # FastAPI REST endpoints
│   ├── dashboard/      # Streamlit dashboard
│   └── main.py         # API entry point
├── tests/              # 54 pytest tests
├── config/             # Prometheus config
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_api.py -v

# Run with coverage
python -m pytest tests/ --cov=src
```

## Known Windows Issues

- **uuid_utils DLL blocked**: Windows Application Control may block the native `_uuid_utils.pyd` extension. The application automatically falls back to pure Python `uuid4()` generation. No configuration changes needed.

## License

MIT License — see [LICENSE](LICENSE) for details.
