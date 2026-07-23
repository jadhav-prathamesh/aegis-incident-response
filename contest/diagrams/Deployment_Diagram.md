# Aegis — "Multi-Agent AI Incident Response Platform"
## Deployment Diagram

## Purpose

Docker Compose deployment topology showing all 7 services, their dependencies, port mappings, and external LLM dependency. Future integrations shown separately.

## Source Traceability

| Service | Image | Port | Depends On | Health Check | Source | Status |
|---|---|---|---|---|---|---|
| api | Custom build | 8000 | postgres, redis | /health | `Dockerfile` | **Implemented** |
| dashboard | Custom build | 8501 | api | /health | `src/dashboard/app.py` | **Implemented** |
| postgres | pgvector/pg16 | 5432 | — | pg_isready | `docker-compose.yml` | **Implemented** |
| redis | redis:7-alpine | 6379 | — | redis-cli ping | `docker-compose.yml` | **Implemented** |
| chroma | chromadb/chroma:latest | 8100 | — | heartbeat API | `docker-compose.yml` | **Implemented** |
| prometheus | prom/prometheus:latest | 9090 | — | /-/healthy | `config/prometheus.yml` | **Implemented** |
| grafana | grafana/grafana:latest | 3000 | prometheus | /health | `docker-compose.yml` | **Implemented** |

## Mermaid Specification

```mermaid
graph TB
    subgraph "Docker Compose (Default Network)"
        API[api<br/>FastAPI :8000]
        DASH[dashboard<br/>Streamlit :8501]
        PG[postgres<br/>pgvector/pg16 :5432]
        RD[redis<br/>7-alpine :6379]
        CH[chroma<br/>chromadb :8100]
        PROM[prometheus<br/>:9090]
        GRAF[grafana<br/>:3000]
    end

    subgraph "Volumes"
        PGV[(pgdata)]
        RDV[(redisdata)]
        CHV[(chromadata)]
        GFV[(grafanadata)]
    end

    subgraph "External Dependencies"
        LLM[OpenRouter API]
    end

    subgraph "Future Integrations (Not Wired)"
        PD[PagerDuty]
        CLOUD[AWS / GCP / Azure]
        SNOW[ServiceNow]
        K8S[Kubernetes]
    end

    API --> PG
    API --> RD
    API --> CH
    API --> LLM
    PROM -.->|scrapes| API
    GRAF --> PROM
    DASH --> API

    PG --> PGV
    RD --> RDV
    CH --> CHV
    GRAF --> GFV

    style API fill:#4a9,color:#fff
    style DASH fill:#4a9,color:#fff
    style PG fill:#a4a,color:#fff
    style RD fill:#a4a,color:#fff
    style CH fill:#a4a,color:#fff
    style PROM fill:#a94,color:#fff
    style GRAF fill:#a94,color:#fff
    style LLM fill:#44a,color:#fff
    style PD fill:#666,color:#fff,stroke-dasharray: 5 5
    style CLOUD fill:#666,color:#fff,stroke-dasharray: 5 5
    style SNOW fill:#666,color:#fff,stroke-dasharray: 5 5
    style K8S fill:#666,color:#fff,stroke-dasharray: 5 5
```

## Status Legend

| Colour | Status |
|---|---|
| Green (#4a9) | Application services — **Implemented** |
| Purple (#a4a) | Data services — **Implemented** |
| Amber (#a94) | Monitoring services — **Implemented** |
| Blue (#44a) | External dependency — **Implemented** |
| Grey dashed (#666) | Future — **Configured but not wired** |

## Validation Criteria

- [ ] All 7 Docker services match `docker-compose.yml` exactly
- [ ] Ports match: 8000, 8501, 5432, 6379, 8100, 9090, 3000
- [ ] Dependencies: api depends on postgres+redis; dashboard depends on api; grafana depends on prometheus
- [ ] Volumes match: pgdata, redisdata, chromadata, grafanadata
- [ ] No custom Docker networks (compose uses default)
- [ ] Future integrations visually distinguished (dashed border, grey)
- [ ] OpenRouter LLM shown as external dependency (not in compose)
