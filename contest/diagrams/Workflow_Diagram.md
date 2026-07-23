# Aegis — "Multi-Agent AI Incident Response Platform"
## Workflow Diagram

## Purpose

Incident management business workflow showing the 7-stage lifecycle: Observe → Reason → Plan → Decide → Execute → Validate → Learn. The Learn stage is a **Future Enhancement** and is visually distinguished.

## Source Traceability

| Stage | Agent | Source | Status |
|---|---|---|---|
| Observe | Observer | `src/agents/observer.py:149-226` | **Implemented** |
| Reason | Orchestrator | `src/agents/orchestrator.py:173-192` | **Implemented** |
| Plan | Planner | `src/agents/planner.py:105-165` | **Implemented** |
| Decide | Orchestrator | `src/agents/orchestrator.py:288-333` | **Implemented** |
| Execute | Executor | `src/agents/executor.py:115-253` | **Implemented** |
| Validate | Validator | `src/agents/validator.py:162-294` | **Implemented** |
| Learn | — | No implementation | **Future Enhancement** |

## Mermaid Specification

```mermaid
stateDiagram-v2
    [*] --> Incident_Created
    Incident_Created --> Observing
    Observing --> Reasoning : Observation Complete
    Reasoning --> Planning : Decision: Plan
    Reasoning --> Escalated : Decision: Escalate
    Planning --> Approval_Required : High Risk
    Planning --> Executing : Low Risk
    Approval_Required --> Executing : Approved
    Approval_Required --> Re_Planning : Rejected
    Executing --> Validating : All Steps Complete
    Executing --> Rolling_Back : Step Failed
    Rolling_Back --> Escalated
    Validating --> Resolved : All Checks Pass
    Validating --> Observing : Check Failed
    Validating --> Escalated : Critical Failure
    Resolved --> [*]
    Escalated --> [*]

    state Learn {
        [*] --> Future_Enhancement
    }
    Resolved --> Learn : post-incident analysis
    Learn --> [*]

    note right of Observing
        Health checks
        Metrics queries
        Alert analysis
        Log scanning
        Dependency checks
    end note

    note right of Planning
        Knowledge base search
        Similar incident lookup
        LLM structured plan
    end note

    note right of Executing
        15 action types
        Approval gates
        Rollback support
    end note

    note right of Validating
        5 check types:
        Health, Metrics, Synthetic,
        Alerts, Compliance, Baselines
    end note

    note right of Learn : Future Enhancement
        Feedback loop from
        validation to planning
        Knowledge base auto-update
        Success rate tracking
    end note
```

## Status Legend

| Stage | Status |
|---|---|
| Observe → Validate | **Implemented** |
| Learn | **Future Enhancement** |

## Validation Criteria

- [ ] All 6 implemented stages match agent implementations in `src/agents/`
- [ ] Decision points match orchestrator routing logic
- [ ] Error paths (rollback, escalate, re-observe) match exception handling
- [ ] Learn stage is labelled **Future Enhancement**, NOT Implemented
- [ ] Validation check count corrected to 5 (matches `src/core/validation.py`)
- [ ] State transitions match `IncidentStatus` enum lifecycle
