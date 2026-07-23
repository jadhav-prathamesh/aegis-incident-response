# Aegis — "Multi-Agent AI Incident Response Platform"
## Future Roadmap

## Purpose

Document planned enhancements, feature-gated capabilities, and long-term vision.

## Source Traceability

| Component | File |
|---|---|
| Feature flags | `src/core/config.py:FeatureFlagsSettings` |
| Agent type enum | `src/core/models.py:AgentType` (unused types) |
| Cloud/K8s tool stubs | `src/agents/executor.py` |
| Project plan | `PROJECT_PLAN.md` |
| Changelog | `CHANGELOG.md` |

## Phase 1 — Completion (Done)

All Phase 1 features are implemented:
- [x] Multi-agent architecture (Orchestrator, Planner, Executor, Observer, Validator)
- [x] ReAct pattern agent framework
- [x] Incident management lifecycle
- [x] REST API (6 route modules)
- [x] Streamlit dashboard
- [x] Vector search (ChromaDB + pgvector)
- [x] Similar incident retrieval
- [x] Action dispatcher (15 action types)
- [x] Approval workflow
- [x] Monitoring and health checks
- [x] Validation and compliance
- [x] Docker deployment
- [x] 93 tests

## Phase 2 — Configured but Not Implemented

These capabilities have settings defined and/or feature flags enabled but no actual implementation:

### Predictive Failure Detection
- **Flag:** `FEATURE_ENABLE_PREDICTIVE_FAILURE = true`
- **Status:** Configured only
- **Required:** Implement failure prediction model or integration

### Intelligent Routing
- **Flag:** `FEATURE_ENABLE_INTELLIGENT_ROUTING = true`
- **Status:** Configured only
- **Required:** Implement ticket routing logic based on incident attributes

## Phase 3 — Stub Integrations

These capabilities have function signatures but return placeholder data:

### Cloud Provider SDK
- **File:** `src/agents/executor.py:379-393`
- **Tool:** `cloud_action()`
- **Status:** Stub — returns `{"success": true, "message": "..."}`
- **Required:** Implement AWS/GCP/Azure SDK calls

### Kubernetes Operator
- **File:** `src/agents/executor.py:362-376`
- **Tool:** `kubernetes_action()`
- **Status:** Stub — returns `{"success": true, "message": "..."}` (separate from kubectl-based action handlers)
- **Required:** Implement K8s API client calls

### ServiceNow Integration
- **File:** `src/agents/executor.py:396-408`
- **Tool:** `servicenow_action()`
- **Status:** Stub — returns placeholder
- **Required:** Implement ServiceNow REST API calls
- **Note:** ServiceNow settings exist in `IntegrationSettings`

### Ticket Creation (External)
- **File:** `src/core/action_dispatcher.py:412-428`
- **Handler:** `_handle_create_ticket()`
- **Status:** Generates mock ticket numbers — no external system integration
- **Required:** Connect to ServiceNow, Jira, or similar

## Phase 4 — Feature-Gated but Disabled

These features have flags set to `false` by default:

| Feature | Flag | Status |
|---|---|---|
| Chaos Engineering | `FEATURE_ENABLE_CHAOS_ENGINEERING = false` | Not implemented |
| Cost Optimization | `FEATURE_ENABLE_COST_OPTIMIZATION = false` | Not implemented |
| GitOps | `FEATURE_ENABLE_GITOPS = false` | Not implemented |

## Phase 5 — Unimplemented Agent Types

The `AgentType` enum defines these types but no agent class exists:

| Agent Type | Purpose | Status |
|---|---|---|
| `RCA_ANALYZER` | Deep root cause analysis | Not implemented |
| `HEALING_AGENT` | Self-healing operations | Not implemented |
| `TICKET_ROUTER` | Intelligent ticket routing | Not implemented |
| `PRIORITIZER` | Incident prioritization | Not implemented |
| `PREDICTOR` | Predictive failure detection | Not implemented |

## Phase 6 — Learning & Feedback Loop

The "Learn" stage of the agentic loop is entirely missing:
- No mechanism to update knowledge base from resolved incidents
- No model fine-tuning or prompt optimization
- No success/failure feedback to improve future decisions
- No incident pattern learning over time

## Phase 7 — Infrastructure

| Item | Status |
|---|---|
| CI/CD pipeline (GitHub Actions) | Not implemented |
| Kubernetes manifests | Not implemented |
| Helm charts | Not implemented |
| Terraform/Pulumi | Not implemented |
| End-to-end tests | Not implemented |
| Load/performance tests | Not implemented |
| Security audit | Not performed |

## Long-Term Vision

Beyond the above phases, the stretch goals include:
- Multi-tenancy support
- Self-hosted LLM support (Ollama, vLLM)
- Real-time incident streaming
- Mobile notifications
- Integration marketplace
- SSO / SAML authentication
- SOC 2 / HIPAA compliance
