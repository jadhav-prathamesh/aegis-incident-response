# Aegis — "Multi-Agent AI Incident Response Platform"
## API Documentation

## Purpose

Complete API reference for all REST endpoints. Every endpoint described here is implemented and testable.

## Source Traceability

| Module | File |
|---|---|
| Health routes | `src/api/routes/health.py` |
| Incident routes | `src/api/routes/incidents.py` |
| Approval routes | `src/api/routes/approvals.py` |
| Agent routes | `src/api/routes/agents.py` |
| Monitoring routes | `src/api/routes/monitoring.py` |
| Validation routes | `src/api/routes/validation.py` |
| FastAPI app | `src/api/app.py` |
| Base path | `/api/v1` (configurable via `API_PREFIX`) |

## Common

- **Base URL:** `http://localhost:8000`
- **API Prefix:** `/api/v1` (default)
- **Format:** JSON
- **Auth:** Not implemented (JWT config exists but middleware is not wired)

## Health Endpoints

### `GET /health`

Liveness probe. Returns `{"status": "healthy", "version": "1.0.0"}`.

Source: `src/api/routes/health.py:12`

### `GET /ready`

Readiness probe. Returns `{"status": "ready"}`.

Source: `src/api/routes/health.py:17`

### `GET /info`

Platform metadata. Returns name, version, environment.

Source: `src/api/routes/health.py:27`

## Incident Endpoints

### `GET /api/v1/incidents`

List all incidents.

**Response:** `list[IncidentResponse]` with id, title, description, severity, status, category, priority, source, affected_services, created_at, root_cause, resolution.

Source: `src/api/routes/incidents.py:95`

### `GET /api/v1/incidents/{incident_id}`

Get incident by ID.

**Response:** `IncidentResponse` or 404.

Source: `src/api/routes/incidents.py:101`

### `POST /api/v1/incidents`

Create a new incident.

**Request body:** `IncidentCreateRequest` with title (required), description (required), severity (default SEV3), category (default UNKNOWN), priority, source, affected_services, affected_resources, tags.

**Response:** `IncidentResponse` with 201.

Source: `src/api/routes/incidents.py:110`

### `PATCH /api/v1/incidents/{incident_id}`

Update an existing incident.

**Request body:** `IncidentUpdateRequest` with status, severity, root_cause, resolution, assigned_to, assigned_team, tags (all optional).

**Response:** Updated `IncidentResponse` or 404.

Source: `src/api/routes/incidents.py:131`

### `GET /api/v1/incidents/{incident_id}/similar`

Find similar incidents.

**Query param:** `limit` (default 5).

**Response:** List of similar incidents with similarity scores.

Source: `src/api/routes/incidents.py:157`

## Approval Endpoints

### `GET /api/v1/approvals/pending`

List pending approval requests.

**Response:** List of `ApprovalResponse` with id, action_type, target_resource, status, created_at.

Source: `src/api/routes/approvals.py:72`

### `POST /api/v1/approvals`

Create a new approval request.

**Request body:** `ApprovalCreateRequest` with action_type, target_resource, parameters, incident_id, execution_id.

**Response:** `ApprovalResponse` with 201.

Source: `src/api/routes/approvals.py:78`

### `POST /api/v1/approvals/{approval_id}/approve`

Approve a pending request.

**Request body:** `ApprovalActionRequest` with approver (default "api-user") and notes.

**Response:** Updated `ApprovalResponse` or 404.

Source: `src/api/routes/approvals.py:91`

### `POST /api/v1/approvals/{approval_id}/reject`

Reject a pending request.

**Request body:** `ApprovalRejectRequest` with rejector (default "api-user") and reason.

**Response:** Updated `ApprovalResponse` or 404.

Source: `src/api/routes/approvals.py:99`

### `GET /api/v1/approvals/{approval_id}`

Get approval request by ID.

**Response:** `ApprovalResponse` or 404.

Source: `src/api/routes/approvals.py:109`

## Agent Endpoints

### `POST /api/v1/agents/execute`

Execute an agent task.

**Request body:** `AgentExecuteRequest` with agent_type, task_type, input_data, context, priority, timeout_seconds.

**Response:** `AgentExecuteResponse` with task_id, agent_type, success, output, error, execution_time_ms, confidence_score.

Source: `src/api/routes/agents.py:40`

### `GET /api/v1/agents/types`

List all available agent types.

**Response:** List of agent type strings.

Source: `src/api/routes/agents.py:70`

### `GET /api/v1/agents/{agent_type}/health`

Check health of a specific agent.

**Response:** Agent health details (initialized, llm_configured, tools_count, config).

Source: `src/api/routes/agents.py:76`

## Monitoring Endpoints

### `GET /api/v1/monitoring/health/{service_name}`

HTTP health check for a service.

Source: `src/api/routes/monitoring.py:23`

### `GET /api/v1/monitoring/tcp/{host}/{port}`

TCP connectivity check.

Source: `src/api/routes/monitoring.py:29`

### `GET /api/v1/monitoring/metrics/{resource_id}`

Query metrics for a resource.

**Query param:** `duration_minutes` (default 30).

Source: `src/api/routes/monitoring.py:35`

### `GET /api/v1/monitoring/prometheus`

Raw Prometheus query.

**Query param:** `query` (PromQL expression).

Source: `src/api/routes/monitoring.py:41`

### `GET /api/v1/monitoring/alerts`

Fetch active alerts.

**Query param:** `resource_ids` (comma-separated).

Source: `src/api/routes/monitoring.py:47`

### `GET /api/v1/monitoring/deployments/{service_name}`

Get recent deployment status.

**Query param:** `namespace` (default "default").

Source: `src/api/routes/monitoring.py:53`

### `POST /api/v1/monitoring/logs`

Analyze logs for anomalies.

**Request body:** JSON with `resource_ids` and `since_minutes`.

Source: `src/api/routes/monitoring.py:59`

### `POST /api/v1/monitoring/correlate`

Correlate events across monitoring systems.

**Request body:** JSON with `resource_ids` and `since_hours`.

Source: `src/api/routes/monitoring.py:69`

## Validation Endpoints

### `POST /api/v1/validation/synthetic`

Run a synthetic test against a service.

**Request body:** `SyntheticTestRequest` with service_name, test_type, endpoint.

Source: `src/api/routes/validation.py:56`

### `POST /api/v1/validation/alerts`

Verify alert resolution for an incident.

**Request body:** `AlertVerifyRequest` with incident_id, resource_ids.

Source: `src/api/routes/validation.py:62`

### `POST /api/v1/validation/compliance`

Run compliance checks.

**Request body:** `ComplianceRequest` with incident_id, execution_id.

Source: `src/api/routes/validation.py:68`

### `POST /api/v1/validation/baselines`

Compare resources against baselines.

**Request body:** `BaselineRequest` with resource_ids.

Source: `src/api/routes/validation.py:74`

### `POST /api/v1/validation/rollback`

Validate a rollback operation.

**Request body:** `RollbackValidateRequest` with execution_id, service_name.

Source: `src/api/routes/validation.py:80`
