# Aegis — "Multi-Agent AI Incident Response Platform"
## Project Structure

## Purpose

Complete file-by-file breakdown of the repository structure.

## Source Traceability

Root: `/mnt/d/Local AI testing/tcs-rio-submission/`

## Directory Tree

```
tcs-rio-submission/
├── .env.example                  # Environment variable template
├── .gitignore                    # Git exclusion rules
├── CHANGELOG.md                  # Version history
├── Dockerfile                    # Container build definition
├── PROJECT_PLAN.md               # Development roadmap
├── README.md                     # Project README
├── docker-compose.yml            # Multi-service Docker configuration
├── pyproject.toml                # Python project configuration
│
├── config/
│   └── prometheus.yml            # Prometheus scrape configuration
│
├── src/
│   ├── __init__.py               # Package init (no exports)
│   └── main.py                   # API server entry point
│   │
│   ├── agents/
│   │   ├── __init__.py           # Package init
│   │   ├── base.py               # BaseAgent, ReactAgent, agent factory
│   │   ├── orchestrator.py       # Orchestrator agent
│   │   ├── planner.py            # Planner agent
│   │   ├── executor.py           # Executor agent
│   │   ├── observer.py           # Observer agent
│   │   └── validator.py          # Validator agent
│   │
│   ├── api/
│   │   ├── __init__.py           # Package init
│   │   ├── app.py                # FastAPI application factory
│   │   └── routes/
│   │       ├── __init__.py       # Package init
│   │       ├── agents.py         # Agent execution endpoints
│   │       ├── approvals.py      # Approval management endpoints
│   │       ├── health.py         # Health/readiness/info endpoints
│   │       ├── incidents.py      # Incident CRUD endpoints
│   │       ├── monitoring.py     # Monitoring query endpoints
│   │       └── validation.py     # Validation endpoints
│   │
│   ├── core/
│   │   ├── __init__.py           # Package init
│   │   ├── action_dispatcher.py  # 15 action handlers
│   │   ├── approval.py           # Approval workflow
│   │   ├── config.py             # 11 settings classes
│   │   ├── database.py           # SQLAlchemy async engine
│   │   ├── embeddings.py         # Embedding service with fallback
│   │   ├── exceptions.py         # 30+ exception classes
│   │   ├── incident_store.py     # In-memory incident repository
│   │   ├── knowledge_base.py     # Hybrid knowledge search
│   │   ├── logging.py            # Structlog configuration
│   │   ├── models.py             # Domain models and enums
│   │   ├── monitoring.py         # Health checks, metrics, alerts
│   │   ├── similar_incidents.py  # Similarity search
│   │   ├── utils.py              # Shared utilities
│   │   ├── validation.py         # Validation services
│   │   └── vector_db.py          # ChromaDB/pgvector clients
│   │
│   └── dashboard/
│       ├── __init__.py           # Package init
│       └── app.py                # Streamlit dashboard
│
├── tests/
│   ├── test_action_dispatcher.py # 8 action dispatcher tests
│   ├── test_agent_orchestrator.py# 26 orchestrator tests
│   ├── test_agent_pipeline.py    # 28 pipeline/agent tests
│   ├── test_api.py               # 8 API endpoint tests
│   ├── test_approval.py          # 6 approval tests
│   ├── test_dashboard.py         # 6 dashboard tests
│   ├── test_planner_search.py    # 3 planner search tests
│   └── test_similar_incidents.py # 3 similarity search tests
│
├── docs/                         # Documentation suite
├── contest/                      # Contest documentation
│   ├── prompts/
│   ├── source/
│   ├── generated/
│   ├── diagrams/
│   ├── presentation/
│   └── review/
│
└── config/
    └── prometheus.yml            # Monitoring configuration
```

## Module Dependency Graph

```
src/main.py
  └── src/core/config.py
  └── uvicorn

src/api/app.py
  └── src/api/routes/*.py
  └── src/core/config.py
  └── src/core/logging.py
  └── fastapi

src/agents/base.py
  └── src/core/config.py
  └── src/core/logging.py
  └── src/core/models.py
  └── langchain_core
  └── langgraph

src/agents/orchestrator.py
  └── src/agents/base.py
  └── src/core/incident_store.py
  └── src/core/similar_incidents.py
  └── src/core/models.py

src/agents/planner.py
  └── src/agents/base.py
  └── src/core/knowledge_base.py
  └── src/core/similar_incidents.py
  └── src/core/models.py

src/agents/executor.py
  └── src/agents/base.py
  └── src/core/action_dispatcher.py
  └── src/core/approval.py

src/agents/observer.py
  └── src/agents/base.py
  └── src/core/monitoring.py

src/agents/validator.py
  └── src/agents/base.py
  └── src/core/validation.py
  └── src/core/monitoring.py

src/dashboard/app.py
  └── src/core/incident_store.py
  └── src/core/approval.py
  └── src/core/models.py
  └── streamlit
```
