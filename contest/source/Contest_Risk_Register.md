# Contest Risk Register

## Purpose

Document all risks identified during development and deployment of Aegis, with mitigation strategies.

## Source Traceability

Risks are identified from: source code analysis (`src/core/config.py`, `src/core/exceptions.py`), deployment configuration (`docker-compose.yml`, `.env.example`), and known gaps documented in the evidence file.

## Risk Ratings

| Rating | Definition |
|---|---|
| **Critical** | Production-blocking, no workaround |
| **High** | Significant operational impact |
| **Medium** | Limited impact, workaround exists |
| **Low** | Minor inconvenience only |

## Technical Risks

| ID | Risk | Likelihood | Impact | Rating | Mitigation |
|---|---|---|---|---|---|
| R1 | LLM API unavailable | Medium | High (agents use fallback) | **High** | Fallback decision engine in orchestrator; degrade gracefully |
| R2 | LLM hallucinates action plan | Low | High (wrong remediation) | **Medium** | Human approval required for high-risk actions; rollback enabled |
| R3 | In-memory incident store lost on restart | High | High (all incidents lost) | **Critical** | Implement PostgreSQL persistent store (planned) |
| R4 | Docker Compose port conflicts | Medium | Medium (services fail) | **Medium** | All ports configurable via environment variables |
| R5 | No authentication exposed | Medium | Critical (unauthorized access) | **Critical** | Deploy behind reverse proxy or VPN (manual mitigation) |
| R6 | Stub integrations produce no real effect | High | Medium (manual remediation required) | **High** | Documented limitation; next sprint items |
| R7 | Thread-safety with global incident store | Medium | Medium (data races) | **Medium** | Add asyncio.Lock (currently unguarded) |
| R8 | ChromaDB vector DB persistence in container | Medium | Low (data lost on restart) | **Low** | Volume mounted in docker-compose |
| R9 | Auto-approve in dev mode | Low (dev only) | High (unintended actions) | **Low** | Dev mode flag; production must configure approval |
| R10 | No health check for LLM dependency | Medium | Medium (silent degradation) | **Medium** | Add `/health` endpoint check for LLM connectivity |

## Project Risks

| ID | Risk | Likelihood | Impact | Rating | Mitigation |
|---|---|---|---|---|---|
| R11 | Incomplete documentation | Low | Medium (user confusion) | **Low** | Automated generation from source code |
| R12 | Scope creep in roadmap | Medium | Medium (delayed delivery) | **Medium** | Priority matrix in roadmap document |
| R13 | Contest submission deadline | Medium | High (missing cut-off) | **High** | All core deliverables complete |
| R14 | Missing learning loop | Low (for MVP) | Medium (no continuous improvement) | **Medium** | Documented as gap; phase 7 priority |

## Security Risks

| ID | Risk | Likelihood | Impact | Rating | Mitigation |
|---|---|---|---|---|---|
| R15 | API key in environment | Medium | High (credential leakage) | **High** | .env excluded from Git; production use secrets manager |
| R16 | Prometheus/Grafana exposed | Medium | Medium (metrics leakage) | **Medium** | Internal network only in docker-compose |
| R17 | No input validation on actions | Low | Medium (malformed actions) | **Low** | Action types are typed (Enum), step parameters are validated |

## Dependency Risks

| ID | Risk | Likelihood | Impact | Rating | Mitigation |
|---|---|---|---|---|---|
| R18 | ChromaDB version mismatch | Low | Medium (vector DB fails) | **Low** | Pinned version in docker-compose |
| R19 | pgvector extension not available | Low | Low (falls back to ChromaDB) | **Low** | Dual vector DB support |
| R20 | structlog version breaking | Low | Low (logging degradation) | **Low** | Pinned in pyproject.toml |

## Risk Summary

| Rating | Count |
|---|---|
| Critical | 2 (R3, R5) |
| High | 3 (R1, R6, R15) |
| Medium | 6 (R2, R4, R7, R10, R12, R13) |
| Low | 5 (R8, R9, R11, R17, R18, R19, R20) |

**Critical items:**
1. **R3 - In-memory store** — Mitigated by database engine being ready; needs wiring.
2. **R5 - No auth** — Mitigated by deployment guidance (behind firewall/VPN).

**High items:**
1. **R1 - LLM unavailable** — Mitigated by fallback engine, but degraded without LLM.
2. **R6 - Stub integrations** — Mitigated by documentation; users know limitations.
3. **R15 - API key leakage** — Mitigated by .gitignore and secrets management guidance.
