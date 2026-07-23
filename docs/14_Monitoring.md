# Aegis — "Multi-Agent AI Incident Response Platform"
## Monitoring

## Purpose

Document the monitoring capabilities: health checks, metrics, alerts, log analysis, and event correlation.

## Source Traceability

| Component | File |
|---|---|
| Monitoring service | `src/core/monitoring.py` |
| Monitoring settings | `src/core/config.py:MonitoringSettings` |
| Prometheus config | `config/prometheus.yml` |
| API monitoring routes | `src/api/routes/monitoring.py` |
| Observer agent | `src/agents/observer.py` |
| Validation checks | `src/core/validation.py` |

## Monitoring Services

All monitoring functions are in `src/core/monitoring.py`.

### Health Checks

#### HTTP Health Check (`check_http_health`)

```python
async def check_http_health(
    url: str,
    timeout: int = 10,
    expected_status: int = 200,
) -> dict[str, Any]:
```

Performs an HTTP GET request and returns:
- `healthy`: bool
- `status_code`: int
- `message`: str
- `body_preview`: first 500 chars of response

#### TCP Health Check (`check_tcp_health`)

```python
async def check_tcp_health(
    host: str,
    port: int,
    timeout: int = 5,
) -> dict[str, Any]:
```

Attempts async TCP connection. Returns `healthy` bool and message.

### Prometheus Integration

#### Query Prometheus (`query_prometheus`)

```python
async def query_prometheus(
    query: str,
    duration_minutes: int = 30,
    step: str = "15s",
) -> dict[str, Any]:
```

Sends a PromQL instant query. Returns status, value, and metric metadata.

#### Resource Metrics (`query_metrics_for_resource`)

```python
async def query_metrics_for_resource(
    resource_id: str,
    duration_minutes: int = 30,
) -> dict[str, Any]:
```

Queries CPU usage and memory usage for a resource identified by instance name. Applies threshold-based health classification:

| Metric | Degraded Threshold | Unhealthy Threshold |
|---|---|---|
| CPU usage | > 75% | > 90% |
| Memory usage | > 80% | > 90% |

### Alertmanager Integration

#### Active Alerts (`get_active_alerts_for_resources`)

```python
async def get_active_alerts_for_resources(
    resource_ids: list[str],
) -> list[dict[str, Any]]:
```

Fetches all alerts from Alertmanager API and filters by matching resource IDs. Returns alert name, severity, status, message, and labels.

### Log Analysis

#### Simple Log Analysis (`analyze_logs_simple`)

```python
async def analyze_logs_simple(
    resource_ids: list[str],
    since_minutes: int = 60,
    error_patterns: list[str] | None = None,
) -> dict[str, Any]:
```

Performs pattern-based analysis. Default patterns: ERROR, FATAL, Traceback, OOMKilled, Connection refused, timeout, panic.

**Note:** This is a simplified implementation. It returns "No anomalies detected" without actually querying log sources. Production implementation would connect to Elasticsearch, Loki, or CloudWatch.

### Kubernetes Deployment Status

#### Deployment Status (`get_deployment_status_k8s`)

```python
async def get_deployment_status_k8s(
    service_name: str,
    namespace: str = "default",
    since_hours: int = 24,
) -> dict[str, Any]:
```

Queries kubectl for recent ScalingReplicaSet events. Returns last 5 deployment events.

### Event Correlation

#### Correlate Events (`correlate_events_across_systems`)

```python
async def correlate_events_across_systems(
    resource_ids: list[str],
    since_hours: int = 24,
) -> dict[str, Any]:
```

Groups active alerts by severity and identifies correlated alert groups (multiple alerts with same severity across resources).

## Observer Agent

The Observer Agent (`src/agents/observer.py`) uses the monitoring services to create a comprehensive `IncidentObservation`:

1. Health checks on all affected services
2. Metrics queries for affected resources
3. Active alerts retrieval
4. Dependency health checks
5. Log analysis

It classifies overall status as:
- **stable** — all healthy, no critical alerts
- **degraded** — some degraded checks
- **degrading** — unhealthy or >2 degraded checks
- **critical** — critical alerts or >2 unhealthy checks

## API Endpoints

See `07_API_Documentation.md` for monitoring API endpoints:
- `GET /api/v1/monitoring/health/{service_name}`
- `GET /api/v1/monitoring/tcp/{host}/{port}`
- `GET /api/v1/monitoring/metrics/{resource_id}`
- `GET /api/v1/monitoring/prometheus`
- `GET /api/v1/monitoring/alerts`
- `GET /api/v1/monitoring/deployments/{service_name}`
- `POST /api/v1/monitoring/logs`
- `POST /api/v1/monitoring/correlate`

## Prometheus Configuration

`config/prometheus.yml`:
- Global scrape interval: 15s
- API scrape interval: 10s
- Scrapes `api:8000/metrics`

## OpenTelemetry

Configurable via environment variables but not actively used in code:
- `MONITORING_OTEL_ENABLED`
- `MONITORING_OTEL_SERVICE_NAME`
- `MONITORING_OTEL_EXPORTER`
- `MONITORING_OTEL_ENDPOINT`

## Current Limitations

- **Log analysis** — Simplified stub that does not query actual log sources
- **Prometheus URL** — Read from config but actual Prometheus instance only available in Docker
- **Alertmanager** — API queried but no webhook receiver configured
- **Metrics endpoint** — FastAPI `/metrics` endpoint not implemented (Prometheus scrapes a non-existent path)
- **OpenTelemetry** — Settings exist but no OTel SDK integration is wired
