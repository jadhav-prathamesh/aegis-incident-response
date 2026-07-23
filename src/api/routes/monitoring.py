"""Monitoring query endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from src.core.monitoring import (
    analyze_logs_simple,
    check_http_health,
    check_tcp_health,
    correlate_events_across_systems,
    get_active_alerts_for_resources,
    get_deployment_status_k8s,
    query_metrics_for_resource,
    query_prometheus,
)

router = APIRouter()


@router.get("/health/{service_name}")
async def service_health(service_name: str) -> dict[str, Any]:
    """HTTP health check for a service."""
    return await check_http_health(f"http://{service_name}/health")


@router.get("/tcp/{host}/{port}")
async def tcp_check(host: str, port: int) -> dict[str, Any]:
    """TCP connectivity check."""
    return await check_tcp_health(host, port)


@router.get("/metrics/{resource_id}")
async def resource_metrics(resource_id: str, duration_minutes: int = 30) -> dict[str, Any]:
    """Query metrics for a resource."""
    return await query_metrics_for_resource(resource_id, duration_minutes)


@router.get("/prometheus")
async def prometheus_query(query: str) -> dict[str, Any]:
    """Raw Prometheus query proxy."""
    return await query_prometheus(query)


@router.get("/alerts")
async def active_alerts(resource_ids: str = "") -> list[dict[str, Any]]:
    """Fetch active alerts, optionally filtered by comma-separated resource IDs."""
    ids = [r.strip() for r in resource_ids.split(",") if r.strip()] if resource_ids else []
    return await get_active_alerts_for_resources(ids)


@router.get("/deployments/{service_name}")
async def deployment_status(service_name: str, namespace: str = "default") -> dict[str, Any]:
    """Get recent deployment status."""
    return await get_deployment_status_k8s(service_name, namespace)


@router.post("/logs")
async def analyze_logs(body: dict[str, Any]) -> dict[str, Any]:
    """Analyze logs for anomalies."""
    return await analyze_logs_simple(
        resource_ids=body.get("resource_ids", []),
        since_minutes=body.get("since_minutes", 60),
    )


@router.post("/correlate")
async def correlate(body: dict[str, Any]) -> dict[str, Any]:
    """Correlate events across monitoring systems."""
    return await correlate_events_across_systems(
        resource_ids=body.get("resource_ids", []),
        since_hours=body.get("since_hours", 24),
    )
