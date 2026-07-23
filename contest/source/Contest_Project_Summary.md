# Aegis — "Multi-Agent AI Incident Response Platform"
## Contest Project Summary

### What It Is

An enterprise-grade multi-agent AI incident response platform that automates production incident management. Aegis uses a multi-agent LangGraph architecture to understand incidents, perform root cause analysis, create remediation plans, execute approved actions, monitor recovery, and validate resolution.

### Key Statistics

| Metric | Value |
|---|---|
| Agents | 5 (Orchestrator, Planner, Executor, Observer, Validator) |
| Action types | 15 (restart, scale, rollback, failover, block, isolate, etc.) |
| Action handlers | All **Implemented** — see `src/core/action_dispatcher.py` |
| Vector DB backends | 2 (ChromaDB, pgvector) — **Implemented** |
| API endpoints | 23 across 6 route modules — **Implemented** |
| Tests | 93 passing — **Implemented** |
| Docker services | 7 (API, Dashboard, PostgreSQL, Redis, ChromaDB, Prometheus, Grafana) |
| Configuration groups | 11 nested settings classes |
| Knowledge base entries | 5 bundled runbooks (seed corpus) — **Implemented** |

### Architecture

Multi-agent orchestration pattern with LangGraph state machines. Each agent has a single responsibility:

1. **Orchestrator** — Receives incidents, makes LLM-driven decisions, coordinates agents
2. **Planner** — Analyses incidents, searches knowledge base, creates remediation plans
3. **Executor** — Executes approved actions with rollback support
4. **Observer** — Monitors system health, metrics, alerts during remediation
5. **Validator** — Validates fixes via synthetic tests, compliance, baseline comparison

### Technology Stack

| Layer | Choice |
|---|---|
| Language | Python 3.12+ |
| AI Framework | LangGraph + LangChain |
| LLM | OpenRouter (configurable to OpenAI, Anthropic, Ollama) |
| Backend | FastAPI |
| Database | PostgreSQL + asyncpg |
| Vector DB | ChromaDB / pgvector |
| Cache | Redis |
| Dashboard | Streamlit |
| Monitoring | Prometheus / Grafana / Alertmanager |
| Logging | Structlog + stdlib fallback |
| Containerization | Docker / Docker Compose |
| Testing | Pytest (93 tests) |

### Source Repository

All source code is in `src/`:
- Agents: `src/agents/` (6 files)
- Core services: `src/core/` (14 files)
- API: `src/api/` (7 files)
- Dashboard: `src/dashboard/` (2 files)
- Tests: `tests/` (8 test files)
