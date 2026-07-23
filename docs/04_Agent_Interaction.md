# Aegis — "Multi-Agent AI Incident Response Platform"
## Agent Interaction

## Purpose

Document how agents communicate, the orchestration protocol, and the message passing between components.

## Source Traceability

| Component | File |
|---|---|
| Orchestrator decision framework | `src/agents/orchestrator.py` |
| Agent task model | `src/core/models.py:AgentTask` |
| Agent result model | `src/core/models.py:AgentResult` |
| Orchestrator decision model | `src/agents/orchestrator.py:OrchestratorDecision` |
| Agent execution | `src/agents/base.py:BaseAgent.execute()` |

## Interaction Protocol

Agents communicate through a **task-result protocol** mediated by the Orchestrator:

```
Orchestrator → [AgentTask] → Agent
Agent → [AgentResult] → Orchestrator
```

### Task Message (`AgentTask`)

Defined in `src/core/models.py:139-154`:

| Field | Type | Purpose |
|---|---|---|
| task_id | UUID | Unique task identifier |
| agent_type | AgentType | Target agent (PLANNER, EXECUTOR, etc.) |
| task_type | str | Action to perform ("plan", "execute", etc.) |
| input_data | dict | Task-specific input payload |
| context | dict | Shared context (incident_id, workflow_id, orchestrator_decision) |
| priority | int (1-10) | Task priority (default 5) |
| timeout_seconds | int | Execution timeout (default 300) |

### Result Message (`AgentResult`)

Defined in `src/core/models.py:157-169`:

| Field | Type | Purpose |
|---|---|---|
| task_id | UUID | Matches the originating task |
| agent_type | AgentType | Source agent |
| success | bool | Whether execution succeeded |
| output | dict | Structured results |
| artifacts | list[dict] | Collected evidence |
| next_actions | list[AgentTask] | Sub-tasks to schedule |
| error | str or None | Error message on failure |
| execution_time_ms | int | Wall-clock execution time |
| tokens_used | int | Token count for billing |
| confidence_score | float (0.0-1.0) | Agent confidence in result |

## Orchestration Flow

### Decision Protocol

The Orchestrator uses a JSON-based decision protocol:

```json
{
  "action": "plan|execute|observe|validate|escalate|close",
  "reason": "Detailed reasoning string",
  "next_agent": "PLANNER|EXECUTOR|OBSERVER|VALIDATOR|null",
  "payload": { ... },
  "confidence": 0.0-1.0
}
```

The decision model is defined in `src/agents/orchestrator.py:31-38`.

### Decision Sources

1. **LLM-based** (`_make_decision()`): Builds context from incident state, agent history, pending approvals → calls LLM → parses JSON response
2. **Fallback rules** (`_fallback_decision()`): Hardcoded if/else logic when LLM fails or is unavailable

### Decision Matrix (Fallback)

| Incident State | Condition | Decision | Next Agent |
|---|---|---|---|
| No incident | Always | plan | PLANNER |
| OPEN, SEV1/SEV2 | Always | plan (high confidence) | PLANNER |
| OPEN, SEV3+ | Always | plan | PLANNER |
| INVESTIGATING | Planner not done | plan | PLANNER |
| INVESTIGATING | Planner done | execute | EXECUTOR |
| RESOLVING/RESOLVED | Validator not done | validate | VALIDATOR |
| RESOLVING/RESOLVED | Validator done | close | None |
| Default (other) | Always | observe | OBSERVER |

### Agent Handoff

Defined in `_execute_decision()` (`src/agents/orchestrator.py:288-333`):

1. Creates `AgentTask` with context from current incident and workflow
2. Stores task in `state.intermediate_results` under key `{AGENT_TYPE}_task`
3. Marks agent as completed in `state.completed_agents`
4. Special handlers for `escalate` (logs warning) and `close` (updates incident status)

## Incident Lifecycle

```
Status Flow:
OPEN → ACKNOWLEDGED → INVESTIGATING → IDENTIFIED → RESOLVING → RESOLVED → CLOSED
  ↓                          ↓              ↓             ↓
Orchestrator           Planner sets     Executor     Validator
receives               root_cause      executes     verifies
incident                                actions
```

## State Sharing

Agents share state through:
1. **Incident model** (`src/core/models.py:Incident`) — shared across all agents via `incident_store`
2. **Task context** — `AgentTask.context` dict carries incident_id, workflow_id, orchestrator_decision
3. **Intermediate results** — Each agent's state stores results in `intermediate_results` dict

## Approval Protocol

High-risk actions require approval before execution:

```
Executor → create_approval_request() → ApprovalRequest (PENDING)
   ↓                                        ↓
Wait (if dev mode)                    Human approves/rejects
   ↓                                        ↓
Continue ✓                          Executor notified
                                       ↓
                                 Continue or rollback
```

The approval workflow is defined in `src/core/approval.py`. Actions requiring approval: RESTART_SERVICE, ROLLBACK_DEPLOYMENT, FAILOVER, ISOLATE_HOST, BLOCK_IP, CUSTOM_SCRIPT, SCALE_DOWN, FLUSH_QUEUE.

## Confidence Scoring

Each agent calculates a confidence score in `BaseAgent._calculate_confidence()` (`src/agents/base.py:228-237`):

| Condition | Score |
|---|---|
| Error occurred | 0.0 |
| Validation passed | 0.95 |
| First iteration | 0.8 |
| Subsequent iterations | max(0.5, 0.9 - i * 0.1) |
