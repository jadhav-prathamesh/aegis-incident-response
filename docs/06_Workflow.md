# Aegis — "Multi-Agent AI Incident Response Platform"
## Workflow

## Purpose

Document the end-to-end incident management workflow from creation to resolution, including all decision points and agent handoffs.

## Source Traceability

| Component | File |
|---|---|
| Orchestrator workflow | `src/agents/orchestrator.py` |
| Planner workflow | `src/agents/planner.py` |
| Executor workflow | `src/agents/executor.py` |
| Observer workflow | `src/agents/observer.py` |
| Validator workflow | `src/agents/validator.py` |
| Incident lifecycle | `src/core/models.py:IncidentStatus` |
| Action dispatch | `src/core/action_dispatcher.py` |

## Complete Incident Workflow

```
┌──────────────────────────────────────────────────────────┐
│                     INCIDENT CREATED                       │
│  API POST /incidents │ Dashboard form │ Monitoring alert  │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│             1. ORCHESTRATOR — RECEIVE & DECIDE             │
│  - Load incident from store                                │
│  - Build decision context (severity, category, status)     │
│  - LLM decision or fallback rules                          │
│  Decision: plan → route to PlannerAgent                    │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│             2. PLANNER — ANALYSE & PLAN                    │
│  - Search knowledge base for relevant runbooks             │
│  - Find similar past incidents                             │
│  - Call LLM for structured RemediationPlan                 │
│  - Return plan with steps, risks, approval requirements    │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│             3. ORCHESTRATOR — REVIEW PLAN                  │
│  - Plan received → decision: execute                      │
│  - Route to ExecutorAgent                                  │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│             4. EXECUTOR — EXECUTE PLAN STEPS               │
│  For each step:                                            │
│  ├─ Check if approval required                             │
│  │    ├─ Yes → request_approval() → wait or reject         │
│  │    └─ No → continue                                     │
│  ├─ Execute action via dispatch_action()                   │
│  │    ├─ Success → next step                               │
│  │    └─ Failure → initiate_rollback()                     │
│  └─ Update incident status                                 │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│             5. OBSERVER — MONITOR & OBSERVE                │
│  - Run health checks on affected services                  │
│  - Query Prometheus metrics                                │
│  - Check active alerts                                     │
│  - Analyze logs for anomalies                              │
│  - Generate observation report + recommendations           │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│             6. ORCHESTRATOR — PROGRESS CHECK               │
│  - Observation received → decision: validate              │
│  - Route to ValidatorAgent                                 │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│             7. VALIDATOR — VERIFY & VALIDATE               │
│  - Health endpoint checks                                  │
│  - Key metrics vs baseline                                 │
│  - Synthetic transactions                                  │
│  - Alert resolution verification                           │
│  - Compliance check                                        │
│  - Produce ValidationReport                                │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│             8. ORCHESTRATOR — RESOLVE OR ESCALATE          │
│  - Validation passed → close incident                     │
│  - Validation failed → escalate to human                  │
│  - Update incident status → CLOSED                        │
└──────────────────────────────────────────────────────────┘
```

## Workflow States

Each state corresponds to an `IncidentStatus` value:

| State | Description | Entry Point |
|---|---|---|
| OPEN | Incident created, awaiting action | API/dashboard |
| ACKNOWLEDGED | Incident seen by system | Orchestrator |
| INVESTIGATING | Planner analysing | Planner start |
| IDENTIFIED | Root cause found | Planner complete |
| RESOLVING | Executor working | Executor start |
| RESOLVED | Actions complete | Executor complete |
| CLOSED | Validated and closed | Validator complete |
| CANCELLED | Manually cancelled | Not auto-triggered |

## Parallel Workflows

The current implementation processes agents sequentially. The `OrchestratorState` tracks `completed_agents` to determine next steps. Parallel execution (e.g., observer running concurrently with executor) is a **Future Enhancement**.

## Approval Workflow

Defined in `src/core/approval.py:210-225`:

```
Action type check → requires_approval()?
  ├─ No → execute immediately
  └─ Yes → create_approval_request()
       ├─ Dev mode + auto_approve → APPROVED immediately
       └─ Production → PENDING → wait for human
            ├─ Approve → execute
            ├─ Reject → rollback
            └─ Timeout → TIMED_OUT
```

Actions that always require approval: RESTART_SERVICE, ROLLBACK_DEPLOYMENT, FAILOVER, ISOLATE_HOST, BLOCK_IP, CUSTOM_SCRIPT, SCALE_DOWN, FLUSH_QUEUE.

## Rollback Workflow

When a step fails and a `rollback_action` is defined:
1. Log the failure with step details
2. Call `initiate_rollback()` tool
3. If rollback succeeds → mark execution `ROLLED_BACK`, continue
4. If rollback fails → mark execution FAILED, set error
5. Update incident status to RESOLVING with failure message

## Escalation Workflow

When the orchestrator decides to escalate:
1. Log escalation event with incident ID and reason
2. Set incident status to ACKNOWLEDGED (for human attention)
3. The system does not implement any notification channel — logging is the only output
