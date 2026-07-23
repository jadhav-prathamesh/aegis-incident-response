# Contest Agentic Workflow

## Purpose

Document the 7-stage agentic workflow demonstrating Observe → Reason → Plan → Decide → Execute → Validate → Learn.

## Source Traceability

| Stage | File | Status |
|---|---|---|
| Observe | `src/agents/observer.py`, `src/core/monitoring.py` | **Implemented** |
| Reason | `src/agents/orchestrator.py:_make_decision()` | **Implemented** (with fallback) |
| Plan | `src/agents/planner.py:_create_plan()` | **Implemented** |
| Decide | `src/agents/orchestrator.py` | **Implemented** |
| Execute | `src/agents/executor.py`, `src/core/action_dispatcher.py` | **Implemented** |
| Validate | `src/agents/validator.py`, `src/core/validation.py` | **Implemented** |
| Learn | — | **Not Implemented** |

## Stage Details

### Stage 1: Observe

**What happens:**

When an incident is created or updated:
1. The Observer Agent identifies affected services and resources from the incident
2. Runs health checks on each service (`check_http_health`)
3. Queries metrics from Prometheus (`query_metrics_for_resource`)
4. Fetches active alerts from Alertmanager (`get_active_alerts_for_resources`)
5. Analyses logs for error patterns (`analyze_logs_simple`)
6. Checks dependency health
7. Correlates events across monitoring systems
8. Produces `IncidentObservation` with overall status and recommendations

**Agentic quality:** The Observer uses LLM for generating contextual recommendations based on observation data. The status determination (`_determine_overall_status`) is rule-based but provides structured data for other agents.

**Source:** `src/agents/observer.py:149-226`

### Stage 2: Reason

**What happens:**

The Orchestrator analyses the incident context:
1. Loads incident from store
2. Builds decision context: severity, category, status, affected services, root cause (if known)
3. Reviews completed agents and pending approvals
4. Considers previous decisions
5. Sends context to LLM for reasoning
6. LLM returns structured decision with action, reason, next_agent, confidence

**Agentic quality:** This is the core reasoning stage. The LLM evaluates multiple factors and decides the optimal next step. The fallback decision engine provides deterministic reasoning when the LLM is unavailable.

**Source:** `src/agents/orchestrator.py:173-192`

### Stage 3: Plan

**What happens:**

The Planner Agent creates a detailed remediation plan:
1. Searches the knowledge base for relevant runbooks (`search_knowledge_entries`)
2. Finds similar past incidents via vector similarity (`find_similar`)
3. Builds comprehensive context: incident details + KB matches + similar incidents
4. Uses LLM `with_structured_output(RemediationPlan)` for typed output
5. Plan includes: ordered steps, dependencies, risk assessment, approval requirements, rollback procedures

**Agentic quality:** The LLM generates a structured plan tailored to the specific incident. The plan includes risk assessment and approval requirements, showing awareness of operational safety.

**Source:** `src/agents/planner.py:105-165`

### Stage 4: Decide

**What happens:**

Based on the plan and current state:
1. Orchestrator receives plan results
2. Determines if the plan requires human approval
3. Routes to Executor Agent for execution
4. If issues are detected (no plan, high-risk), may decide to escalate

**Agentic quality:** The Orchestrator makes context-aware routing decisions. It tracks which agents have completed their work and what approvals are pending, enabling intelligent workflow progression.

**Source:** `src/agents/orchestrator.py:288-333`

### Stage 5: Execute

**What happens:**

The Executor Agent executes each plan step:
1. For each step, checks if approval is required
2. If approval required: `request_approval()` → wait for human or auto-approve (dev mode)
3. If approved: `execute_action()` dispatches to appropriate handler
4. 15 action types available: restart, scale, rollback, clear cache, flush queue, failover, block IP, isolate host, run diagnostic, collect logs, create ticket, notify, escalate, custom script
5. On step failure: `initiate_rollback()` if rollback action defined
6. Updates incident status throughout execution

**Agentic quality:** The executor is procedural but integrates human-in-the-loop for critical actions. Rollback capability shows awareness of failure modes.

**Source:** `src/agents/executor.py:115-253`

### Stage 6: Validate

**What happens:**

The Validator Agent verifies the fix:
1. Health endpoint checks on all affected services
2. Key metrics comparison against baselines
3. Synthetic transactions (smoke tests)
4. Alert resolution verification
5. Compliance check against policies
6. Baseline comparison for regression detection
7. Produces `ValidationReport` with pass/fail per check

**Agentic quality:** Multi-dimensional validation ensures the fix is complete. Compliance checks show awareness of operational policies beyond just "is it running?"

**Source:** `src/agents/validator.py:162-294`

### Stage 7: Learn (Missing)

**What should happen:**

The system should learn from each incident to improve future responses:
- Update knowledge base with successful remediation patterns
- Adjust confidence scores based on historical success rates
- Fine-tune or optimize prompts based on outcomes
- Identify patterns in recurring incidents

**Why it's missing:**
- No feedback loop from validation results to planning
- No mechanism to update the seed knowledge corpus
- No success/failure tracking per action type
- No model fine-tuning or prompt optimization

**Status:** **Future Enhancement**

## Workflow Diagram

```
Incident Created
    │
    ▼
┌──────────┐
│ OBSERVE  │ ← Health checks, metrics, alerts, logs
└────┬─────┘
    │
    ▼
┌──────────┐
│ REASON   │ ← Orchestrator LLM analysis
└────┬─────┘
    │
    ▼
┌──────────┐
│  PLAN    │ ← Knowledge base + similar incidents + LLM plan
└────┬─────┘
    │
    ▼
┌──────────┐
│  DECIDE  │ ← Route to executor or escalate
└────┬─────┘
    │
    ▼
┌──────────┐
│ EXECUTE  │ ← Approved actions with rollback
└────┬─────┘
    │
    ▼
┌──────────┐
│ VALIDATE │ ← Health, metrics, synthetic, compliance
└────┬─────┘
    │
    ▼
┌──────────┐
│  LEARN   │ ← NOT IMPLEMENTED
└──────────┘
    │
    ▼
 Incident Closed or Escalated
```
