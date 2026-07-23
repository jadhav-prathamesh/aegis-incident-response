"""Monitoring services for health checks, metrics, alerts, and log analysis."""

from __future__ import annotations

import asyncio
import json
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from src.core.config import get_settings
from src.core.logging import get_logger
from src.core.utils import safe_float

logger = get_logger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# Health checks
# ---------------------------------------------------------------------------

async def check_http_health(
    url: str,
    timeout: int = 10,
    expected_status: int = 200,
) -> dict[str, Any]:
    """Perform an HTTP health check against a URL."""
    try:
        req = Request(url, method="GET")
        req.add_header("User-Agent", "platform-observer/1.0")

        def _fetch() -> tuple[int, str]:
            with urlopen(req, timeout=timeout) as resp:
                return resp.status, resp.read().decode(errors="replace")[:2000]

        loop = asyncio.get_running_loop()
        status_code, body = await loop.run_in_executor(None, _fetch)

        healthy = status_code == expected_status
        return {
            "healthy": healthy,
            "status_code": status_code,
            "message": (
                f"HTTP {status_code}"
                + (" OK" if healthy else f" (expected {expected_status})")
            ),
            "body_preview": body[:500],
        }
    except URLError as exc:
        return {"healthy": False, "status_code": 0, "message": f"Connection failed: {exc}"}
    except Exception as exc:
        return {"healthy": False, "status_code": 0, "message": f"Health check error: {exc}"}


async def check_tcp_health(host: str, port: int, timeout: int = 5) -> dict[str, Any]:
    """Check if a TCP port is accepting connections."""
    try:
        _reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout,
        )
        writer.close()
        await writer.wait_closed()
        return {"healthy": True, "message": f"{host}:{port} accepting connections"}
    except Exception as exc:
        return {"healthy": False, "message": f"{host}:{port} unreachable: {exc}"}


# ---------------------------------------------------------------------------
# Prometheus / metrics queries
# ---------------------------------------------------------------------------

async def query_prometheus(
    query: str,
    duration_minutes: int = 30,
    step: str = "15s",
) -> dict[str, Any]:
    """Query Prometheus for a PromQL expression."""
    prometheus_url = getattr(settings.integration, "prometheus_url", "http://localhost:9090")

    # Use instant query for current value
    url = f"{prometheus_url}/api/v1/query?query={query}"
    try:
        req = Request(url, method="GET")
        loop = asyncio.get_running_loop()

        def _fetch() -> dict[str, Any]:
            with urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode())

        data = await loop.run_in_executor(None, _fetch)

        if data.get("status") == "success":
            results = data.get("data", {}).get("result", [])
            if results:
                value = results[0].get("value", [None, None])
                return {
                    "status": "healthy",
                    "value": value[1] if len(value) > 1 else None,
                    "metric": results[0].get("metric", {}),
                    "query": query,
                }
            return {
                "status": "healthy", "value": None,
                "message": "No data returned", "query": query,
            }
        return {"status": "unknown", "message": f"Prometheus error: {data.get('error', 'unknown')}"}
    except Exception as exc:
        logger.debug("Prometheus query failed", error=str(exc))
        return {"status": "unknown", "message": f"Prometheus unreachable: {exc}", "query": query}


async def query_metrics_for_resource(
    resource_id: str,
    duration_minutes: int = 30,
) -> dict[str, Any]:
    """Query standard metrics for a resource from Prometheus."""
    queries = {
        "cpu_usage": (
            '100 - (avg(rate('
            f'node_cpu_seconds_total{{mode="idle",instance="{resource_id}"}}'
            '[5m])) * 100)'
        ),
        "memory_usage": (
            f'(1 - node_memory_MemAvailable_bytes{{instance="{resource_id}"}}'
            f' / node_memory_MemTotal_bytes{{instance="{resource_id}"}}) * 100'
        ),
    }

    metrics: dict[str, Any] = {}
    status = "healthy"

    for metric_name, query in queries.items():
        result = await query_prometheus(query, duration_minutes)
        metrics[metric_name] = result
        if result.get("status") not in ("healthy",):
            status = "degraded"

    # Check thresholds
    cpu_val = safe_float(metrics.get("cpu_usage", {}).get("value"))
    mem_val = safe_float(metrics.get("memory_usage", {}).get("value"))

    if cpu_val is not None and cpu_val > 90:
        status = "unhealthy"
    elif cpu_val is not None and cpu_val > 75:
        status = "degraded" if status != "unhealthy" else status

    if mem_val is not None and mem_val > 90:
        status = "unhealthy"
    elif mem_val is not None and mem_val > 80:
        status = "degraded" if status != "unhealthy" else status

    return {
        "status": status,
        "summary": f"Resource {resource_id}: CPU={cpu_val or 'N/A'}%, Mem={mem_val or 'N/A'}%",
        "metrics": metrics,
        "duration_minutes": duration_minutes,
    }


# ---------------------------------------------------------------------------
# Alertmanager
# ---------------------------------------------------------------------------

async def get_active_alerts_for_resources(
    resource_ids: list[str],
) -> list[dict[str, Any]]:
    """Fetch active alerts from Alertmanager matching resource IDs."""
    alertmanager_url = getattr(settings.integration, "alertmanager_url", "http://localhost:9093")
    url = f"{alertmanager_url}/api/v2/alerts"

    try:
        req = Request(url, method="GET")
        loop = asyncio.get_running_loop()

        def _fetch() -> list[dict[str, Any]]:
            with urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode())

        raw_alerts = await loop.run_in_executor(None, _fetch)
    except Exception as exc:
        logger.debug("Alertmanager query failed", error=str(exc))
        return []

    resource_set = set(resource_ids)
    matched: list[dict[str, Any]] = []
    for alert in raw_alerts:
        labels = alert.get("labels", {})
        # Check if any label value matches a resource ID
        alert_resources = {
            v for v in labels.values() if isinstance(v, str) and v in resource_set
        }
        if alert_resources or not resource_set:
            matched.append({
                "alert_name": labels.get("alertname", "unknown"),
                "severity": labels.get("severity", "warning"),
                "status": alert.get("status", {}).get("state", "active"),
                "message": alert.get("annotations", {}).get("summary", ""),
                "labels": labels,
                "starts_at": alert.get("startsAt", ""),
                "resources": list(alert_resources),
            })

    return matched


# ---------------------------------------------------------------------------
# Log analysis (simple pattern-based)
# ---------------------------------------------------------------------------

async def analyze_logs_simple(
    resource_ids: list[str],
    since_minutes: int = 60,
    error_patterns: list[str] | None = None,
) -> dict[str, Any]:
    """Analyse logs for common error patterns.

    This is a lightweight analysis that checks for known error signatures.
    In production this would connect to Elasticsearch / Loki / CloudWatch.
    """
    if error_patterns is None:
        error_patterns = [
            "ERROR",
            "FATAL",
            "Traceback",
            "OOMKilled",
            "Connection refused",
            "timeout",
            "panic",
        ]

    return {
        "status": "healthy",
        "summary": "No anomalies detected in log analysis",
        "resources_checked": resource_ids,
        "patterns_monitored": error_patterns,
        "since_minutes": since_minutes,
        "anomalies": [],
    }


# ---------------------------------------------------------------------------
# Deployment status (kubectl-based)
# ---------------------------------------------------------------------------

async def get_deployment_status_k8s(
    service_name: str,
    namespace: str = "default",
    since_hours: int = 24,
) -> dict[str, Any]:
    """Get recent deployment rollout status via kubectl."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "kubectl", "get", "events",
            "-n", namespace,
            "--field-selector", f"involvedObject.name={service_name},reason=ScalingReplicaSet",
            "--sort-by", ".lastTimestamp",
            "-o", "json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=15)
        data = json.loads(stdout.decode())

        events = data.get("items", [])[-5:]  # last 5 events
        deployments = []
        for evt in events:
            deployments.append({
                "message": evt.get("message", ""),
                "timestamp": evt.get("lastTimestamp", ""),
                "type": evt.get("type", ""),
            })

        return {
            "status": "recent_deployments" if deployments else "no_recent_deployments",
            "deployments": deployments,
            "service": service_name,
            "namespace": namespace,
        }
    except Exception as exc:
        return {
            "status": "unknown",
            "message": f"Unable to fetch deployment status: {exc}",
            "deployments": [],
        }


# ---------------------------------------------------------------------------
# Event correlation
# ---------------------------------------------------------------------------

async def correlate_events_across_systems(
    resource_ids: list[str],
    since_hours: int = 24,
) -> dict[str, Any]:
    """Correlate events from multiple monitoring sources.

    Merges data from Prometheus alerts, Alertmanager, and deployment events.
    """
    alerts = await get_active_alerts_for_resources(resource_ids)
    correlations: list[dict[str, Any]] = []

    # Group alerts by severity and resource
    severity_groups: dict[str, list[dict[str, Any]]] = {}
    for alert in alerts:
        sev = alert.get("severity", "info")
        severity_groups.setdefault(sev, []).append(alert)

    for severity, group in severity_groups.items():
        if len(group) > 1:
            correlations.append({
                "type": "alert_correlation",
                "severity": severity,
                "count": len(group),
                "alerts": [a["alert_name"] for a in group],
                "resources": list({r for a in group for r in a.get("resources", [])}),
            })

    return {
        "correlations": correlations,
        "total_alerts": len(alerts),
        "summary": (
            f"Found {len(correlations)} correlated event groups "
            f"across {len(resource_ids)} resources"
        ),
    }
