# Aegis — "Multi-Agent AI Incident Response Platform"
## Agent Interaction Diagram

## Purpose

Runtime communication flow showing how an incident progresses through the agent pipeline: creation → observation → reasoning → planning → approval → execution → validation → closure.

## Source Traceability

| Step | Agent | Source | State Transition |
|---|---|---|---|
| Incident Created | Orchestrator | `src/api/routes/incidents.py:111` | OPEN |
| Observe | Observer | `src/agents/observer.py` | INVESTIGATING |
| Reason | Orchestrator | `src/agents/orchestrator.py:_make_decision()` | INVESTIGATING |
| Plan | Planner | `src/agents/planner.py:_create_plan()` | PLANNING |
| Approve | Executor | `src/core/approval.py` | PENDING_APPROVAL |
| Execute | Executor | `src/agents/executor.py:115-253` | EXECUTING |
| Validate | Validator | `src/agents/validator.py:162-294` | VALIDATING |
| Close | Orchestrator | `src/agents/orchestrator.py` | RESOLVED → CLOSED |

## Mermaid Specification

```mermaid
sequenceDiagram
    participant User as User / Alert
    participant API as FastAPI
    participant ORC as Orchestrator
    participant OBS as Observer
    participant PLN as Planner
    participant EXE as Executor
    participant VAL as Validator
    participant LLM as OpenRouter LLM
    participant KB as Knowledge Base

    User->>API: POST /incidents
    API->>ORC: new incident (OPEN)
    ORC->>OBS: delegate observation
    OBS->>OBS: health checks, metrics, alerts, logs
    OBS-->>ORC: IncidentObservation

    ORC->>LLM: analyze context & decide
    LLM-->>ORC: structured decision
    ORC->>PLN: delegate planning

    PLN->>KB: search runbooks
    PLN->>KB: find similar incidents
    PLN->>LLM: generate remediation plan
    LLM-->>PLN: RemediationPlan
    PLN-->>ORC: plan (with risk assessment)

    alt high risk or requires approval
        ORC->>EXE: request approval
        EXE->>User: approval required
        User-->>EXE: approved
    end

    EXE->>EXE: execute action (15 types)
    EXE-->>ORC: ExecutionResult

    alt step failed
        EXE->>EXE: initiate rollback
    end

    ORC->>VAL: delegate validation
    VAL->>VAL: 5 check types:
    Note over VAL: health, metrics,<br/>synthetic, alerts,<br/>compliance, baselines
    VAL-->>ORC: ValidationReport

    alt validation passed
        ORC->>API: resolve incident
        API-->>User: 200 OK (RESOLVED)
    else validation failed
        ORC->>OBS: re-observe
    end
```

## Flow Diagram

```mermaid
graph TB
    START[Incident Created] --> OBSERVE[Observe<br/>Investigate services]
    OBSERVE --> REASON[Reason<br/>LLM analysis]
    REASON --> PLAN[Plan<br/>KB + LLM plan]
    PLAN --> APPROVE{Approve?}
    APPROVE -->|yes| EXECUTE[Execute<br/>Action dispatch]
    APPROVE -->|no| REJECT[Re-plan / Escalate]
    EXECUTE --> OK{Success?}
    OK -->|yes| VALIDATE[Validate<br/>5 check types]
    OK -->|no| ROLLBACK[Rollback]
    ROLLBACK --> ESCALATE[Escalate to Human]
    VALIDATE --> PASSED{Passed?}
    PASSED -->|yes| CLOSE[Incident Closed]
    PASSED -->|no| OBSERVE
    REJECT --> REASON

    style START fill:#4a9,color:#fff
    style OBSERVE fill:#4a9,color:#fff
    style REASON fill:#4a9,color:#fff
    style PLAN fill:#4a9,color:#fff
    style EXECUTE fill:#4a9,color:#fff
    style VALIDATE fill:#4a9,color:#fff
    style CLOSE fill:#4a9,color:#fff
    style APPROVE fill:#e8e8e8,color:#333
    style OK fill:#e8e8e8,color:#333
    style PASSED fill:#e8e8e8,color:#333
    style REJECT fill:#a94,color:#fff
    style ROLLBACK fill:#a94,color:#fff
    style ESCALATE fill:#a94,color:#fff
```

## Labels

- **Implemented:** All steps (Observe, Reason, Plan, Approve, Execute, Validate, Close)
- **Implemented:** LLM interaction, Knowledge Base search, Action dispatch, Rollback

## Validation Criteria

- [ ] Sequence of agents matches `src/agents/orchestrator.py` routing logic
- [ ] Each agent's role matches its implementation in `src/agents/`
- [ ] Feedback loop (re-observe on validation failure) matches `src/agents/validator.py` response handling
- [ ] Approval gate matches `src/core/approval.py`
- [ ] Rollback path matches `src/agents/executor.py:initiate_rollback()`
