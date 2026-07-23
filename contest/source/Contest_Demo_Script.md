# Contest Demo Script

## Purpose

A step-by-step script demonstrating Aegis's capabilities. Designed as a live, repeatable demo.

## Prerequisites

```bash
# Start the platform
docker-compose up -d

# Verify all services
curl http://localhost:8000/health

# Open dashboard
open http://localhost:8501
```

## Demo Walkthrough

### 1. Platform Overview (2 minutes)

Show the dashboard: `http://localhost:8501`

- **Current state:** "No incidents" state — empty state presented
- **Architecture:** Quick explainer of 5 agents + vector DB + knowledge base
- **Actions:** Show 15 supported action types

**Narrator:** "This is Aegis — a multi-agent AI incident response platform. It can detect, diagnose, plan remediation, execute fixes, and validate results."

### 2. Trigger an Incident (2 minutes)

From API or dashboard:

```bash
curl -X POST http://localhost:8000/incidents \
  -H "Content-Type: application/json" \
  -d '{
    "id": "inc-001",
    "title": "Production API Latency Spike",
    "severity": "critical",
    "category": "performance",
    "description": "API endpoint /api/v1/orders returning 5 second latency, p99 > 10s",
    "affected_services": ["api-gateway", "order-service"],
    "status": "open"
  }'
```

**What to watch:**
- Dashboard updates with new incident
- Status changes: open → observing → planning → approved → executing → validating → resolved (shown on UI)

**Narrator:** "I'll create a critical incident... The Observer agent immediately begins health checks and metric analysis. You can see the status updating in real-time."

### 3. Agent Pipeline Execution (3 minutes)

Watch the automation flow:

1. **Observer** starts health checks on api-gateway, order-service
2. **Orchestrator** receives observation, reasons about next action
3. **Planner** searches knowledge base, finds similar incidents, creates plan
4. **Executor** processes each step (approval required for critical)

**What to show:**
- Use `GET /incidents/inc-001` to see full incident state
- Show logs:
  ```bash
  docker-compose logs api | tail -50
  ```

**Narrator:** "The Observer has identified the affected services and checked their health. Now the Orchestrator is evaluating the situation — it will determine whether this incident requires a simple fix like scaling the service, or a more complex remediation."

### 4. Knowledge Base Interaction (1 minute)

Show vector search:

```bash
# Search knowledge base
curl "http://localhost:8000/knowledge/search?query=database%20connection%20pool%20exhaustion"
```

**Narrator:** "The Planner searches our knowledge base using vector similarity. It found runbooks for similar latency incidents — this helps it create a targeted remediation plan."

### 5. Approval Workflow (1 minute)

Show approval needed:

```bash
# Check pending approvals
curl http://localhost:8000/approvals/pending

# Approve
curl -X POST http://localhost:8000/approvals/approve -H "Content-Type: application/json" \
  -d '{"approval_id": "step-1", "approved": true, "comment": "Proceed with scaling"}'
```

**Narrator:** "This action requires human approval because it involves restarting a critical service. Once approved, the Executor proceeds."

### 6. Validation (1 minute)

Show validation results:

```bash
curl http://localhost:8000/incidents/inc-001/validation
```

**Narrator:** "After execution, the Validator runs 6 checks — health endpoints, metrics, synthetic transactions, alert clearance, compliance, and baselines. You can see all checks passed."

### 7. End-to-End Summary (1 minute)

Final incident state:

```bash
curl http://localhost:8000/incidents/inc-001 | python -m json.tool
```

Show:
- Full decision trail
- Actions executed
- Validation results
- Total time from creation to resolution

**Narrator:** "The complete incident lifecycle is captured here — from initial observation through to validation. Total time from incident creation to automated resolution: approximately 30 seconds."

### 8. Edge Case: Approve/Reject (1 minute)

```bash
# Create incident requiring approval
curl -X POST http://localhost:8000/incidents -H "Content-Type: application/json" \
  -d '{"id": "inc-002", "title": "Database Connection Pool Exhaustion", ...}'

# Reject an action
curl -X POST http://localhost:8000/approvals/reject -H "Content-Type: application/json" \
  -d '{"approval_id": "step-1", "reason": "Need to verify during maintenance window"}'
```

**Narrator:** "If the engineer rejects a proposed action, the Orchestrator re-evaluates and proposes an alternative."

## Demo Environment Setup

Before the demo:

1. Start all services: `docker-compose up -d`
2. Wait for healthy: Check `http://localhost:8000/health`
3. Verify LLM connectivity: Check API logs for "llm configured"
4. Reset state if needed: `docker-compose down && docker-compose up -d`

## Total Demo Time: ~12 minutes

| Segment | Duration |
|---|---|
| Platform Overview | 2 min |
| Trigger Incident | 2 min |
| Agent Pipeline | 3 min |
| Knowledge Base | 1 min |
| Approval | 1 min |
| Validation | 1 min |
| Summary | 1 min |
| Edge Case | 1 min |
| **Total** | **12 min** |
