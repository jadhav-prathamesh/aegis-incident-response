# Aegis — "Multi-Agent AI Incident Response Platform"
## Validation

## Purpose

Document validation services for verifying remediation success, including synthetic tests, compliance checks, baseline comparison, and rollback validation.

## Source Traceability

| Component | File |
|---|---|
| Validation service | `src/core/validation.py` |
| Validator agent | `src/agents/validator.py` |
| API validation routes | `src/api/routes/validation.py` |
| Monitoring dependency | `src/core/monitoring.py` |
| Utility functions | `src/core/utils.py` |

## Validation Services

All validation logic is in `src/core/validation.py`.

### 1. Synthetic Tests (`run_synthetic_test`)

```python
async def run_synthetic_test(
    service_name: str,
    test_type: str = "smoke",
    endpoint: str | None = None,
    timeout: int = 15,
) -> dict[str, Any]:
```

Performs an HTTP health check against a service endpoint. Returns:
- `passed`: Whether the HTTP check returned expected status
- `message`: Result message
- `duration_ms`: Response time in milliseconds
- `test_type`: The test type identifier
- `target`: The URL tested

### 2. Alert Resolution Verification (`verify_alert_resolution`)

```python
async def verify_alert_resolution(
    incident_id: str,
    resource_ids: list[str],
) -> dict[str, Any]:
```

Checks if all active alerts for the incident's resources have resolved. Returns:
- `all_resolved`: bool
- `total_alerts`: int
- `unresolved_count`: int
- `unresolved_alerts`: list of alert details
- `summary`: Human-readable result

### 3. Compliance Check (`check_incident_compliance`)

```python
async def check_incident_compliance(
    incident_id: str,
    execution_id: str | None = None,
) -> dict[str, Any]:
```

Verifies incident handling against policy rules:
1. **incident_documented** — Title and description must be present (always passes)
2. **actions_logged** — Execution ID must be provided (checked against input)
3. **timeline_met** — SLA timeline compliance (always passes — no SLA engine implemented)

Returns `compliant` status, rule counts, and any violations.

### 4. Baseline Comparison (`compare_resource_baselines`)

```python
async def compare_resource_baselines(
    resource_ids: list[str],
    baseline_window_hours: int = 24,
) -> dict[str, Any]:
```

Compares current CPU metrics against 24-hour historical baseline. Flags deviations >20% as anomalies.

### 5. Rollback Validation (`validate_rollback_completion`)

```python
async def validate_rollback_completion(
    execution_id: str,
    service_name: str | None = None,
    namespace: str = "default",
) -> dict[str, Any]:
```

Verifies rollback success by:
1. Checking Kubernetes rollout status (`kubectl rollout status`)
2. Checking service health endpoint

Returns validation result with details per check.

## Validator Agent

The Validator Agent (`src/agents/validator.py:162-294`) runs all configured validation checks and produces a `ValidationReport`:

### Required Checks

Configured via `validation_config.required_checks` (default):
| Check | Source | What It Validates |
|---|---|---|
| `health_endpoint` | `check_service_health` tool | All affected services return healthy |
| `key_metrics` | `query_metrics` tool | Resource metrics within baseline |
| `synthetic_transaction` | `run_synthetic_test` tool | Service responds to smoke test |
| `alert_resolution` | `verify_alert_resolution` tool | All alerts resolved |
| `compliance` | `check_compliance` tool | Incident handling follows policy |
| `baseline_comparison` | `compare_baselines` tool | Resource metrics vs historical baseline |

### Validation Report

```python
class ValidationReport(BaseModel):
    incident_id: UUID
    validation_id: UUID
    overall_status: str  # "passed", "failed", "partial"
    passed_checks: int
    failed_checks: int
    warning_checks: int
    total_checks: int
    checks: list[ValidationResult]
    summary: str
    recommendations: list[str]
    timestamp: datetime
```

Overall status determination:
- **Passed** — Zero critical failures
- **Failed** — One or more critical failures

## API Endpoints

See `07_API_Documentation.md` for validation API endpoints:
- `POST /api/v1/validation/synthetic`
- `POST /api/v1/validation/alerts`
- `POST /api/v1/validation/compliance`
- `POST /api/v1/validation/baselines`
- `POST /api/v1/validation/rollback`

## Current Limitations

- **Compliance rules** — Only 3 basic rules, no SLA engine, no policy-as-code integration
- **Baseline thresholds** — Hardcoded 20% deviation threshold
- **Log analysis** — Simplified, does not connect to ELK/Loki
- **Synthetic tests** — HTTP health check only, no multi-step transaction testing
- **Kubernetes dependency** — Rollback validation requires kubectl on the host
