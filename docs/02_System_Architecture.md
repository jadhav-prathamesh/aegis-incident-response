# Aegis — "Multi-Agent AI Incident Response Platform"
## System Architecture

## Purpose

Describe the high-level system architecture, component boundaries, and data flow between modules.

## Source Traceability

| Component | File(s) |
|---|---|
| Application configuration | `src/core/config.py` |
| Database layer | `src/core/database.py` |
| Agent framework | `src/agents/base.py` |
| API layer | `src/api/app.py`, `src/api/routes/` |
| Dashboard | `src/dashboard/app.py` |
| Container definitions | `docker-compose.yml`, `Dockerfile` |

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                     External Systems                     │
│  Prometheus │ Alertmanager │ PagerDuty │ ServiceNow     │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                    FastAPI (Port 8000)                    │
│  /health │ /api/v1/incidents │ /api/v1/agents            │
│  /api/v1/approvals │ /api/v1/monitoring                  │
│  /api/v1/validation                                       │
└──────────┬──────────────────────────────────┬────────────┘
           │                                  │
┌──────────▼──────────┐        ┌──────────────▼──────────┐
│   Streamlit Dashboard│        │    Multi-Agent Engine    │
│   (Port 8501)       │        │    (LangGraph)           │
└─────────────────────┘        │    ┌─────────────────┐  │
                               │    │ Orchestrator    │  │
                               │    │ Incident → Decision││
                               │    └────────┬────────┘  │
                               │         ┌───┼───┐       │
                               │    ┌────▼┐ │ ┌─▼─────┐  │
                               │    │Planner│ │ │Observer│  │
                               │    └──┬───┘ │ └───┬───┘  │
                               │    ┌──▼───┐ │ ┌───▼───┐  │
                               │    │Executor│ ││Validator││
                               │    └──┬───┘ │ └───┬───┘  │
                               └───────┼─────┼─────┼──────┘
                                       │     │     │
         ┌─────────────────────────────┼─────┼─────┼──────┐
         │          Core Services      │     │     │      │
         │  ┌──────────┐ ┌──────────┐ │     │     │      │
         │  │ Postgres │ │  Redis   │ │     │     │      │
         │  │ +pgvector│ │          │ │     │     │      │
         │  └──────────┘ └──────────┘ │     │     │      │
         │  ┌──────────┐ ┌──────────┐ │     │     │      │
         │  │ ChromaDB │ │Prometheus│ │     │     │      │
         │  └──────────┘ └──────────┘ │     │     │      │
         └────────────────────────────┼─────┼─────┼──────┘
                                      │     │     │
         ┌────────────────────────────┼─────┼─────┼────────┐
         │      Action Targets        │     │     │        │
         │  Kubectl │ Docker │ SSH │ iptables │ redis-cli │
         └──────────────────────────────────────────────────┘
```

## Module Layer Overview

### 1. API Layer (`src/api/`)
FastAPI application with six route modules: health, incidents, approvals, agents, monitoring, validation. Each route maps to core service functions.

### 2. Agent Layer (`src/agents/`)
Five LangGraph-based agents with a shared base class (`BaseAgent`) and ReAct pattern (`ReactAgent`):
- **OrchestratorAgent** — Decision-making, agent coordination
- **PlannerAgent** — Remediation plan creation
- **ExecutorAgent** — Action execution with approval
- **ObserverAgent** — Monitoring and observation
- **ValidatorAgent** — Validation and compliance

### 3. Core Services Layer (`src/core/`)
Domain logic and shared services:
- `models.py` — Pydantic domain models and enums
- `exceptions.py` — Typed exception hierarchy
- `config.py` — 11 nested settings groups
- `database.py` — SQLAlchemy async engine
- `embeddings.py` — Embedding service with local fallback
- `vector_db.py` — ChromaDB and pgvector clients
- `knowledge_base.py` — Hybrid knowledge search
- `incident_store.py` — In-memory incident repository
- `approval.py` — Approval workflow
- `action_dispatcher.py` — 15 action handlers
- `monitoring.py` — Health checks, metrics, alerts
- `validation.py` — Synthetic tests, compliance, baselines
- `similar_incidents.py` — Vector + brute-force similarity search
- `logging.py` — Structured logging with structlog
- `utils.py` — Shared utility functions

### 4. Dashboard Layer (`src/dashboard/`)
Streamlit application providing operational overview, incident browsing, approval management, and incident creation.

## Data Flow

1. **Incident Ingestion:** API (`POST /api/v1/incidents`) or dashboard create incident → stored in memory → indexed for similarity search
2. **Orchestration:** Orchestrator receives incident → LLM decision → routes to appropriate agent
3. **Planning:** Planner queries vector DB for similar incidents + knowledge base → creates structured RemediationPlan
4. **Execution:** Executor iterates through plan steps → requests approval for risky actions → dispatches via action_dispatcher
5. **Observation:** Observer runs health checks, metric queries, alert checks → provides situational awareness
6. **Validation:** Validator runs synthetic tests, compliance checks, baseline comparisons → produces ValidationReport
7. **Resolution:** Orchestrator receives validation results → marks incident resolved or escalates

## Key Architectural Decisions

| Decision | Rationale | File |
|---|---|---|
| In-memory store (initial) | Enables zero-dependency development and testing | `src/core/incident_store.py` |
| Hybrid vector/local search | Graceful degradation when vector DB unavailable | `src/core/knowledge_base.py` |
| Abstract vector DB client | Swap ChromaDB/pgvector without changing business logic | `src/core/vector_db.py` |
| Agent factory pattern | Centralized agent instantiation with lazy initialization | `src/agents/base.py:get_agent()` |
| Feature flags | Disable capabilities without code changes | `src/core/config.py:FeatureFlagsSettings` |
