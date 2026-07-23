"""
Observer Agent - Continuously monitors incidents and system health.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from langchain_core.tools import BaseTool, tool
from pydantic import BaseModel, Field

from src.agents.base import BaseAgentState, ReactAgent
from src.core.config import get_settings
from src.core.logging import get_logger
from src.core.models import (
    Incident,
    IncidentSeverity,
)
from src.core.monitoring import (
    analyze_logs_simple,
    check_http_health,
    correlate_events_across_systems,
    get_active_alerts_for_resources,
    get_deployment_status_k8s,
    query_metrics_for_resource,
)

logger = get_logger(__name__)
settings = get_settings()


class ObservationResult(BaseModel):
    """Result of a single observation check (health, metric, log, alert, or dependency)."""

    check_id: str
    check_type: str  # health, metric, log, alert, dependency
    target: str
    status: str  # healthy, degraded, unhealthy, unknown
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    severity: IncidentSeverity = IncidentSeverity.SEV5


class IncidentObservation(BaseModel):
    """Aggregated observation snapshot for an incident, including checks, alerts, and recommendations."""

    incident_id: UUID
    observation_id: UUID
    overall_status: str  # stable, improving, degrading, critical
    checks: list[ObservationResult]
    alerts: list[dict[str, Any]] = Field(default_factory=list)
    metrics_summary: dict[str, Any] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ObserverState(BaseAgentState):
    """State for the observer agent, tracking monitoring config and consecutive degraded checks."""

    incident: Incident | None = None
    observation: IncidentObservation | None = None
    monitoring_config: dict[str, Any] = Field(default_factory=dict)
    check_interval_seconds: int = 60
    last_check: datetime | None = None
    consecutive_degraded: int = 0


class ObserverAgent(ReactAgent):
    """Agent that monitors incident progress and system health."""

    def _get_specific_prompt(self) -> str:
        return (
            "You are the Observer Agent responsible for continuous "
            "monitoring of incidents and infrastructure.\n\n"
            "Your responsibilities:\n"
            "1. Continuously monitor incident-related metrics and health checks\n"
            "2. Track alert status changes (firing, acknowledged, resolved)\n"
            "3. Monitor dependency health and cascading effects\n"
            "4. Detect anomalies and patterns in real-time\n"
            "5. Provide situational awareness to other agents\n"
            "6. Generate observations with actionable recommendations\n"
            "7. Alert orchestrator when intervention needed\n\n"
            "Available tools:\n"
            "- check_service_health: Check health of specific services\n"
            "- query_metrics: Query time-series metrics from Prometheus/Datadog\n"
            "- get_active_alerts: Get current alerts for incident resources\n"
            "- check_dependencies: Verify health of dependent services\n"
            "- analyze_logs: Analyze recent logs for anomalies\n"
            "- get_deployment_status: Check recent deployments\n"
            "- correlate_events: Correlate events across systems\n\n"
            "Output: Structured IncidentObservation with overall status "
            "and recommendations."
        )

    def _get_tools(self) -> list[BaseTool]:
        return [
            check_service_health,
            query_metrics,
            get_active_alerts,
            check_dependencies,
            analyze_logs,
            get_deployment_status,
            correlate_events,
        ]

    def _get_state_class(self) -> type[BaseAgentState]:
        return ObserverState

    async def _process_task(self, state: ObserverState) -> ObserverState:
        """Process observation task."""
        task = state.task
        if not task:
            state.error = "No task provided"
            state.should_continue = False
            return state

        # Get incident
        incident_id = task.context.get("incident_id") or task.input_data.get("incident_id")
        if incident_id:
            state.incident = await self._get_incident(incident_id)

        if not state.incident:
            state.error = "No incident found for observation"
            state.should_continue = False
            return state

        # Get monitoring config
        state.monitoring_config = task.input_data.get("monitoring_config", {})
        state.check_interval_seconds = state.monitoring_config.get("interval_seconds", 60)

        # Perform observation
        observation = await self._perform_observation(state)
        state.observation = observation
        state.intermediate_results["observation"] = observation.model_dump()

        # Determine if should continue monitoring
        if observation.overall_status in ["critical", "degrading"]:
            state.consecutive_degraded += 1
            state.should_continue = True
        else:
            state.consecutive_degraded = 0
            state.should_continue = False

        state.last_check = datetime.now(UTC)
        return state

    async def _perform_observation(self, state: ObserverState) -> IncidentObservation:
        """Run all observation checks: health, metrics, alerts, dependencies, and logs."""
        incident = state.incident
        checks = []

        # Check affected services health
        for service in incident.affected_services:
            health = await check_service_health.ainvoke({"service_name": service})
            checks.append(ObservationResult(
                check_id=f"health_{service}",
                check_type="health",
                target=service,
                status=health.get("status", "unknown"),
                message=health.get("message", ""),
                details=health,
            ))

        # Query key metrics for affected resources
        for resource in incident.affected_resources:
            metrics = await query_metrics.ainvoke({
                "resource_id": resource,
                "duration_minutes": 30,
            })
            checks.append(ObservationResult(
                check_id=f"metrics_{resource}",
                check_type="metric",
                target=resource,
                status=metrics.get("status", "unknown"),
                message=metrics.get("summary", ""),
                details=metrics,
            ))

        # Get active alerts
        alerts = await get_active_alerts.ainvoke({
            "resource_ids": incident.affected_resources,
        })

        # Check dependencies
        for resource in incident.affected_resources:
            deps = await check_dependencies.ainvoke({"resource_id": resource})
            checks.append(ObservationResult(
                check_id=f"deps_{resource}",
                check_type="dependency",
                target=resource,
                status=deps.get("status", "unknown"),
                message=deps.get("message", ""),
                details=deps,
            ))

        # Analyze recent logs
        logs_analysis = await analyze_logs.ainvoke({
            "resource_ids": incident.affected_resources,
            "since_minutes": 60,
        })
        checks.append(ObservationResult(
            check_id="logs_analysis",
            check_type="log",
            target="affected_resources",
            status=logs_analysis.get("status", "unknown"),
            message=logs_analysis.get("summary", ""),
            details=logs_analysis,
        ))

        # Determine overall status
        overall_status = self._determine_overall_status(checks, alerts)

        # Generate recommendations
        recommendations = self._generate_recommendations(checks, alerts, incident)

        return IncidentObservation(
            incident_id=incident.id,
            observation_id=uuid4(),
            overall_status=overall_status,
            checks=checks,
            alerts=alerts,
            metrics_summary=self._summarize_metrics(checks),
            recommendations=recommendations,
        )

    def _determine_overall_status(
        self,
        checks: list[ObservationResult],
        alerts: list[dict[str, Any]],
    ) -> str:
        """Determine overall observation status from check results and active alerts."""
        unhealthy_count = sum(1 for c in checks if c.status == "unhealthy")
        degraded_count = sum(1 for c in checks if c.status == "degraded")
        critical_severities = {"SEV1", "SEV2"}
        critical_alerts = sum(
            1 for a in alerts if a.get("severity", "") in critical_severities
        )

        if critical_alerts > 0 or unhealthy_count > 2:
            return "critical"
        elif unhealthy_count > 0 or degraded_count > 2:
            return "degrading"
        elif degraded_count > 0:
            return "degraded"
        return "stable"

    def _generate_recommendations(
        self,
        checks: list[ObservationResult],
        alerts: list[dict[str, Any]],
        incident: Incident,
    ) -> list[str]:
        """Generate actionable recommendations."""
        recommendations = []

        unhealthy_checks = [c for c in checks if c.status == "unhealthy"]
        if unhealthy_checks:
            for check in unhealthy_checks:
                recommendations.append(f"Investigate {check.target}: {check.message}")

        degraded_checks = [c for c in checks if c.status == "degraded"]
        if degraded_checks:
            for check in degraded_checks[:3]:
                recommendations.append(f"Monitor {check.target} closely: {check.message}")

        critical_severities = {"SEV1", "SEV2"}
        critical_alerts = [a for a in alerts if a.get("severity", "") in critical_severities]
        if critical_alerts:
            for alert in critical_alerts:
                recommendations.append(f"Critical alert: {alert.get('message', '')}")

        if incident.severity in [IncidentSeverity.SEV1, IncidentSeverity.SEV2]:
            recommendations.append("High severity incident - consider engaging on-call engineer")

        return recommendations[:10]  # Limit recommendations

    def _summarize_metrics(self, checks: list[ObservationResult]) -> dict[str, Any]:
        """Aggregate metric check results into a summary with healthy/degraded/unhealthy counts."""
        metric_checks = [c for c in checks if c.check_type == "metric"]
        return {
            "total_checks": len(metric_checks),
            "healthy": sum(1 for c in metric_checks if c.status == "healthy"),
            "degraded": sum(1 for c in metric_checks if c.status == "degraded"),
            "unhealthy": sum(1 for c in metric_checks if c.status == "unhealthy"),
        }


# Tools for Observer Agent
@tool
async def check_service_health(service_name: str) -> dict[str, Any]:
    """Check health of a specific service."""
    logger.info("Checking service health", service=service_name)
    http_result = await check_http_health(f"http://{service_name}/health")
    return {
        "status": "healthy" if http_result["healthy"] else "unhealthy",
        "message": http_result["message"],
        "checks": [http_result],
    }


@tool
async def query_metrics(
    resource_id: str,
    duration_minutes: int = 30,
) -> dict[str, Any]:
    """Query time-series metrics for a resource."""
    logger.info("Querying metrics", resource=resource_id, duration=duration_minutes)
    return await query_metrics_for_resource(resource_id, duration_minutes)


@tool
async def get_active_alerts(
    resource_ids: list[str],
) -> list[dict[str, Any]]:
    """Get active alerts for resources."""
    logger.info("Getting active alerts", resources=resource_ids)
    return await get_active_alerts_for_resources(resource_ids)


@tool
async def check_dependencies(resource_id: str) -> dict[str, Any]:
    """Check health of dependent services."""
    logger.info("Checking dependencies", resource=resource_id)
    http_result = await check_http_health(f"http://{resource_id}/health")
    return {
        "status": "healthy" if http_result["healthy"] else "degraded",
        "message": http_result["message"],
        "dependencies": [resource_id],
    }


@tool
async def analyze_logs(
    resource_ids: list[str],
    since_minutes: int = 60,
) -> dict[str, Any]:
    """Analyze recent logs for anomalies."""
    logger.info("Analyzing logs", resources=resource_ids, since=since_minutes)
    return await analyze_logs_simple(resource_ids, since_minutes)


@tool
async def get_deployment_status(
    service_name: str,
    since_hours: int = 24,
) -> dict[str, Any]:
    """Get recent deployment status."""
    logger.info("Getting deployment status", service=service_name)
    return await get_deployment_status_k8s(service_name, since_hours=since_hours)


@tool
async def correlate_events(
    resource_ids: list[str],
    since_hours: int = 24,
) -> dict[str, Any]:
    """Correlate events across monitoring systems."""
    logger.info("Correlating events", resources=resource_ids)
    return await correlate_events_across_systems(resource_ids, since_hours)


# Export
__all__ = [
    "IncidentObservation",
    "ObservationResult",
    "ObserverAgent",
    "ObserverState",
]
