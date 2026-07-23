# Aegis — "Multi-Agent AI Incident Response Platform"
## Project Overview

## Purpose

This document provides a high-level overview of **Aegis**, a multi-agent AI incident response platform for automated production incident management.

## Source Traceability

| Component | File |
|---|---|
| Application entry point | `src/main.py` |
| Application settings | `src/core/config.py:Settings` |
| API application | `src/api/app.py` |
| Dashboard | `src/dashboard/app.py` |
| Project metadata | `pyproject.toml` |

## What It Is

Aegis automates the full incident lifecycle: ingestion, understanding, root cause analysis, remediation planning, execution, monitoring, and validation. It mimics the workflow of an experienced production support engineer using a multi-agent AI architecture built on LangGraph.

### Core Capabilities

| Capability | Status | Source |
|---|---|---|
| Incident creation and management | **Implemented** | `src/core/incident_store.py` |
| Multi-agent LLM orchestration | **Implemented** | `src/agents/orchestrator.py` |
| Remediation planning with vector search | **Implemented** | `src/agents/planner.py` |
| Action execution with approval gates | **Implemented** | `src/agents/executor.py` |
| System monitoring and health checks | **Implemented** | `src/agents/observer.py` |
| Validation and compliance | **Implemented** | `src/agents/validator.py` |
| REST API | **Implemented** | `src/api/routes/` |
| Streamlit dashboard | **Implemented** | `src/dashboard/app.py` |
| Docker deployment | **Implemented** | `Dockerfile`, `docker-compose.yml` |
| PostgreSQL / pgvector support | **Configured** | `src/core/database.py`, `src/core/vector_db.py` |
| Redis caching | **Configured** | `src/core/config.py:RedisSettings` |
| Cloud provider integration | **Stub** | `src/agents/executor.py:cloud_action` |
| Kubernetes integration | **Stub** | `src/agents/executor.py:kubernetes_action` |
| ServiceNow integration | **Stub** | `src/agents/executor.py:servicenow_action` |

## Architecture Philosophy

The platform follows a **multi-agent orchestration pattern** where:

1. The **Orchestrator** receives incidents and makes LLM-driven decisions about workflow
2. The **Planner** analyses the incident and creates a remediation plan
3. The **Executor** executes approved actions with rollback support
4. The **Observer** monitors system health during and after remediation
5. The **Validator** verifies the fix via synthetic tests, compliance, and baselines

## Technology Stack

| Layer | Technology | Implementation |
|---|---|---|
| Language | Python 3.12+ | `pyproject.toml` target-version |
| AI Framework | LangGraph + LangChain | `src/agents/base.py` |
| LLM Provider | OpenRouter (configurable) | `src/core/config.py:LLMSettings` |
| Vector Database | ChromaDB / pgvector | `src/core/vector_db.py` |
| Database | PostgreSQL (asyncpg) | `src/core/database.py` |
| Cache | Redis | `src/core/config.py:RedisSettings` |
| API Framework | FastAPI | `src/api/app.py` |
| Dashboard | Streamlit | `src/dashboard/app.py` |
| Monitoring | Prometheus / Grafana | `config/prometheus.yml` |
| Logging | Structlog + stdlib fallback | `src/core/logging.py` |
| Containerization | Docker / Compose | `Dockerfile`, `docker-compose.yml` |

## Current Status

- **Implemented features:** All core agent workflows, REST API, dashboard, Docker deployment
- **Tests:** 93 passing (unit + behavioural)
- **Documentation:** Complete README, in-code docstrings, generated docs suite
- **Stretch goals:** Cloud SDK integrations, Kubernetes operator, CI/CD pipeline — not yet implemented

## Design Decisions

- **In-memory incident store** (`src/core/incident_store.py`): Kept lightweight until persistent storage is wired in. The database engine (`src/core/database.py`) is fully configured but not yet used by the incident store.
- **Hybrid search** (`src/core/knowledge_base.py`): Falls back from vector DB to a deterministic seed corpus when no vector DB is available.
- **Enum values as strings** (`src/core/models.py`): `use_enum_values=True` stores enums as plain strings to avoid serialization issues.
