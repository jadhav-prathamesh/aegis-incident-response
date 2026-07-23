# Contest Solution Architecture

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    External Integrations                       │
│  Prometheus │ Alertmanager │ PagerDuty │ ServiceNow (Stub)    │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                    FastAPI (Port 8000)                         │
│  /health │ /api/v1/incidents │ /api/v1/agents                 │
│  /api/v1/approvals │ /api/v1/monitoring │ /api/v1/validation   │
└────────────────────┬─────────────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────────────┐
│  Streamlit Dashboard (Port 8501)                              │
│  Overview │ Incidents │ Approvals │ Create Incident           │
└────────────────────┬─────────────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────────────┐
│              Multi-Agent Engine (LangGraph)                    │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                    Orchestrator                          │ │
│  │  Incident → Decision → Route │ Fallback Decision Engine │ │
│  └────────┬──────────┬──────────┬──────────┬───────────────┘ │
│           │          │          │          │                  │
│     ┌─────▼──┐ ┌────▼───┐ ┌───▼────┐ ┌───▼──────┐           │
│     │Planner │ │Executor│ │Observer│ │Validator  │           │
│     │  RCA   │ │Actions │ │Health  │ │Validation │           │
│     │  Plans │ │Approval│ │Metrics │ │Compliance │           │
│     └───┬────┘ │Rollback│ │Alerts  │ │Synthetic  │           │
│         │      └───┬────┘ │Logs    │ │Baselines  │           │
│         │          │      └───┬────┘ └─────┬──────┘           │
│         └──────────┼──────────┼────────────┘                  │
└────────────────────┼──────────┼──────────────────────────────┘
                     │          │
         ┌───────────┼──────────┼──────────────────────────────┐
         │  Core Services       │                              │
         │  PostgreSQL │ Redis │ ChromaDB │ File System        │
         └───────────┼──────────┼──────────────────────────────┘
                     │          │
         ┌───────────┼──────────┼──────────────────────────────┐
         │  Action Targets      │                              │
         │  kubectl │ Docker │ SSH │ iptables │ redis-cli       │
         └──────────────────────────────────────────────────────┘
```

## Layered Architecture

### Layer 1: API Layer (`src/api/`)
- **Framework:** FastAPI
- **Routes:** 6 modules (health, incidents, approvals, agents, monitoring, validation)
- **Purpose:** External interface for incident management, agent execution, monitoring queries, and validation

### Layer 2: Agent Layer (`src/agents/`)
- **Framework:** LangGraph with LangChain
- **Agents:** 5 specialized agents with shared base class
- **Pattern:** ReAct (Reasoning + Acting) with typed state graphs
- **Communication:** Task-result protocol mediated by Orchestrator

### Layer 3: Core Services (`src/core/`)
- **Services:** 14 modules covering domain models, configuration, database, vector search, knowledge management, action dispatch, approval workflow, monitoring, validation, logging
- **Pattern:** Modular, dependency-injected, configurable via pydantic-settings

### Layer 4: Infrastructure (`Docker`, `config/`)
- **Containerization:** Docker + Docker Compose (7 services)
- **Monitoring:** Prometheus + Grafana configuration
- **Database:** PostgreSQL with asyncpg, ChromaDB, Redis

## Key Architecture Decisions

| Decision | Rationale |
|---|---|
| Abstract `VectorDBClient` | Swap between ChromaDB and pgvector without changing agent code |
| Hybrid search fallback | System works without vector DB (seed corpus + brute force) |
| In-memory incident store | Zero-dependency development; PostgreSQL engine ready for migration |
| `use_enum_values=True` | Avoids enum serialization issues in LLM prompts and API responses |
| Feature flags via `FeatureFlagsSettings` | Toggle capabilities without code changes |
| Agent factory with lazy init | Agents initialized on first use, reducing startup time |

## Security Architecture

**Current:** CORS middleware only. No authentication, encryption, or authorization implemented.

**Configured:** JWT settings, rate limiting parameters, audit logging flag — all present in config but not wired.

## Deployment Architecture

- **Local:** `python -m src.main`
- **Docker:** `docker-compose up -d` (7 containers)
- **Production:** Requires additional security, persistence, and scaling changes (see `docs/09_Deployment_Guide.md`)
