# Aegis — "Multi-Agent AI Incident Response Platform"
## High Level Architecture

## Purpose

Enterprise architecture showing Users → Dashboard → FastAPI → AI Agents → Data Layer → External Integrations.

## Source Traceability

| Component | Source | Status |
|---|---|---|
| Streamlit Dashboard | `src/dashboard/app.py` | **Implemented** |
| FastAPI (port 8000) | `src/api/app.py`, `src/main.py` | **Implemented** |
| AI Agents (5) | `src/agents/` | **Implemented** |
| PostgreSQL + pgvector | `src/core/database.py`, `docker-compose.yml` | **Implemented** (data engine) |
| Redis | `src/core/config.py`, `docker-compose.yml` | **Implemented** (cache engine) |
| ChromaDB | `src/core/vector_db.py`, `docker-compose.yml` | **Implemented** |
| Prometheus | `src/core/monitoring.py`, `docker-compose.yml` | **Implemented** |
| Grafana | `docker-compose.yml` | **Implemented** |
| LLM (OpenRouter) | `src/core/config.py`, `src/agents/base.py` | **Implemented** |
| PagerDuty | `src/core/config.py` | **Configured (not wired)** |
| Alertmanager | `src/core/monitoring.py` | **Implemented** |
| Cloud SDKs | `src/agents/executor.py:379-393` | **Stub** |
| ServiceNow | `src/agents/executor.py:396-408` | **Stub** |
| Kubernetes | `src/agents/executor.py:362-376` | **Stub** |

## Mermaid Specification

```mermaid
graph TB
    subgraph "Users"
        DEV[Developer / Operator]
    end

    subgraph "Presentation"
        DASH[Streamlit Dashboard<br/>:8501]
    end

    subgraph "API Layer"
        API[FastAPI<br/>:8000]
    end

    subgraph "Multi-Agent Engine"
        ORC[Orchestrator]
        OBS[Observer]
        PLN[Planner]
        EXE[Executor]
        VAL[Validator]
    end

    subgraph "Data Layer"
        PG[(PostgreSQL<br/>+ pgvector<br/>:5432)]
        RD[(Redis<br/>:6379)]
        CH[(ChromaDB<br/>:8100)]
    end

    subgraph "Monitoring"
        PROM[Prometheus<br/>:9090]
        GRAF[Grafana<br/>:3000]
        ALERT[Alertmanager<br/>:9093]
    end

    subgraph "External AI"
        LLM[OpenRouter API<br/>LLM + Embeddings]
    end

    subgraph "External Integrations"
        CLOUD[AWS / GCP / Azure<br/>Stub]
        SNOW[ServiceNow<br/>Stub]
        K8S[Kubernetes<br/>Stub]
    end

    DEV --> DASH
    DEV --> API
    DASH --> API
    API --> ORC
    ORC --> OBS
    ORC --> PLN
    ORC --> EXE
    ORC --> VAL
    OBS --> PROM
    OBS --> ALERT
    PLN --> CH
    PLN --> PG
    EXE --> CLOUD
    EXE --> SNOW
    EXE --> K8S
    VAL --> PROM
    API --> LLM
    API --> PG
    API --> RD
    PROM --> API
    GRAF --> PROM

    style DEV fill:#e8e8e8,color:#333
    style DASH fill:#4a9,color:#fff
    style API fill:#4a9,color:#fff
    style ORC fill:#4a9,color:#fff
    style OBS fill:#4a9,color:#fff
    style PLN fill:#4a9,color:#fff
    style EXE fill:#4a9,color:#fff
    style VAL fill:#4a9,color:#fff
    style PG fill:#a4a,color:#fff
    style RD fill:#a4a,color:#fff
    style CH fill:#a4a,color:#fff
    style PROM fill:#a94,color:#fff
    style GRAF fill:#a94,color:#fff
    style ALERT fill:#a94,color:#fff
    style LLM fill:#44a,color:#fff
    style CLOUD fill:#666,color:#fff
    style SNOW fill:#666,color:#fff
    style K8S fill:#666,color:#fff
```

## Status Legend

| Colour | Status |
|---|---|
| Green (#4a9) | **Implemented** — code exists and is wired |
| Purple (#a4a) | **Implemented** — service configured, engine ready |
| Amber (#a94) | **Implemented** — configured and running |
| Blue (#44a) | **Implemented** — external dependency |
| Grey (#666) | **Stub** — function exists, returns placeholder |

## Validation Criteria

- [ ] All 7 Docker services from `docker-compose.yml` represented
- [ ] Agent count matches 5 implemented agents in `src/agents/`
- [ ] Stub integrations visually distinguished (grey)
- [ ] Relationship direction matches actual data flow
- [ ] Port numbers match docker-compose.yml
