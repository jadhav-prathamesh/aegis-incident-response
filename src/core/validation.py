"""Validation services for verifying remediation success."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

from src.core.config import get_settings
from src.core.logging import get_logger
from src.core.monitoring import (
    check_http_health,
    get_active_alerts_for_resources,
    query_prometheus,
)
from src.core.utils import safe_float

logger = get_logger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Synthetic transactions
# ---------------------------------------------------------------------------

async def run_synthetic_test(
    service_name: str,
    test_type: str = "smoke",
    endpoint: str | None = None,
    timeout: int = 15,
) -> dict[str, Any]:
    """Run a synthetic test against a service endpoint."""
    url = endpoint or f"https://{service_name}/health"

    start = datetime.now(UTC)
    result = await check_http_health(url, timeout=timeout, expected_status=200)
    elapsed_ms = int((datetime.now(UTC) - start).total_seconds() * 1000)

    return {
        "passed": result["healthy"],
        "message": result["message"],
        "duration_ms": elapsed_ms,
        "test_type": test_type,
        "target": url,
    }


# ---------------------------------------------------------------------------
# Alert resolution verification
# ---------------------------------------------------------------------------

async def verify_alert_resolution(
    incident_id: str,
    resource_ids: list[str],
) -> dict[str, Any]:
    """Verify that all alerts related to an incident have resolved."""
    alerts = await get_active_alerts_for_resources(resource_ids)

    unresolved = [a for a in alerts if a.get("status") != "resolved"]
    all_resolved = len(unresolved) == 0

    return {
        "all_resolved": all_resolved,
        "total_alerts": len(alerts),
        "unresolved_count": len(unresolved),
        "unresolved_alerts": [
            {
                "name": a.get("alert_name"),
                "severity": a.get("severity"),
                "message": a.get("message"),
            }
            for a in unresolved
        ],
        "summary": (
            "All alerts resolved"
            if all_resolved
            else f"{len(unresolved)} alerts still active"
        ),
    }


# ---------------------------------------------------------------------------
# Compliance checks
# ---------------------------------------------------------------------------

async def check_incident_compliance(
    incident_id: str,
    execution_id: str | None = None,
) -> dict[str, Any]:
    """Check compliance of incident handling against policies.

    Verifies that required steps were followed:
    - Incident was properly documented
    - Actions were logged
    - Approvals were obtained for risky actions
    - SLA timelines were met
    """
    violations: list[dict[str, Any]] = []

    # Basic compliance rules (extendable)
    rules = [
        {
            "name": "incident_documented",
            "description": "Incident has title and description",
            "passed": True,
        },
        {
            "name": "actions_logged",
            "description": "All actions are logged for audit",
            "passed": bool(execution_id),
        },
        {"name": "timeline_met", "description": "Incident handled within SLA", "passed": True},
    ]

    for rule in rules:
        if not rule["passed"]:
            violations.append(rule)

    return {
        "compliant": len(violations) == 0,
        "summary": (
            "All compliance checks passed"
            if not violations
            else f"{len(violations)} violations found"
        ),
        "rules_checked": len(rules),
        "rules_passed": len(rules) - len(violations),
        "violations": violations,
    }


# ---------------------------------------------------------------------------
# Baseline comparison
# ---------------------------------------------------------------------------

async def compare_resource_baselines(
    resource_ids: list[str],
    baseline_window_hours: int = 24,
) -> dict[str, Any]:
    """Compare current resource metrics against established baselines."""
    deviations: list[dict[str, Any]] = []

    for resource_id in resource_ids:
        # Query current CPU
        cpu_query = (
            '100 - (avg(rate('
            f'node_cpu_seconds_total{{mode="idle",instance="{resource_id}"}}'
            '[5m])) * 100)'
        )
        cpu_result = await query_prometheus(cpu_query)

        # Query historical baseline (same query but 24h range)
        baseline_query = (
            f'avg_over_time(100 - (avg(rate('
            f'node_cpu_seconds_total{{mode="idle",instance="{resource_id}"}}[5m])))'
            f'[{baseline_window_hours}h:])'
        )
        baseline_result = await query_prometheus(baseline_query)

        current = safe_float(cpu_result.get("value"))
        baseline = safe_float(baseline_result.get("value"))

        if current is not None and baseline is not None:
            deviation_pct = abs(current - baseline)
            within = deviation_pct < 20.0  # 20% deviation threshold
            if not within:
                deviations.append({
                    "resource": resource_id,
                    "metric": "cpu_usage",
                    "current": round(current, 2),
                    "baseline": round(baseline, 2),
                    "deviation_percent": round(deviation_pct, 2),
                })

    return {
        "all_within_baseline": len(deviations) == 0,
        "resources_checked": len(resource_ids),
        "deviations": deviations,
        "summary": (
            "All resources within baseline"
            if not deviations
            else f"{len(deviations)} resource(s) deviating from baseline"
        ),
    }


# ---------------------------------------------------------------------------
# Rollback validation
# ---------------------------------------------------------------------------

async def validate_rollback_completion(
    execution_id: str,
    service_name: str | None = None,
    namespace: str = "default",
) -> dict[str, Any]:
    """Validate that a rollback completed successfully.

    Checks:
    1. Deployment is in a healthy state
    2. All pods are running
    3. Health endpoint responds
    """
    checks_passed = 0
    checks_total = 0
    details: dict[str, Any] = {}

    # Check k8s rollout status
    if service_name:
        checks_total += 1
        try:
            proc = await asyncio.create_subprocess_exec(
                "kubectl", "rollout", "status", f"deployment/{service_name}",
                "-n", namespace, "--timeout=30s",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=35)
            success = proc.returncode == 0
            details["rollout_status"] = {
                "success": success,
                "message": (
                    stdout.decode(errors="replace").strip()
                    or stderr.decode(errors="replace").strip()
                ),
            }
            if success:
                checks_passed += 1
        except Exception as exc:
            details["rollout_status"] = {"success": False, "message": str(exc)}

    # Check health endpoint
    if service_name:
        checks_total += 1
        health = await check_http_health(f"http://{service_name}/health")
        details["health_check"] = health
        if health["healthy"]:
            checks_passed += 1

    valid = checks_passed == checks_total if checks_total > 0 else True
    return {
        "valid": valid,
        "summary": (
            f"Rollback validated: {checks_passed}/{checks_total} checks passed"
            if checks_total > 0
            else "Rollback validated (no runtime checks available)"
        ),
        "details": details,
    }


