"""
Validator Agent - Validates remediation actions and incident resolutions.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from langchain_core.tools import BaseTool, tool
from pydantic import BaseModel, Field

from src.agents.base import BaseAgentState, ReactAgent
from src.core.config import get_settings
from src.core.logging import get_logger
from src.core.models import Incident
from src.core.monitoring import check_http_health, query_metrics_for_resource
from src.core.validation import (
    check_incident_compliance as _check_incident_compliance,
)
from src.core.validation import (
    compare_resource_baselines as _compare_resource_baselines,
)
from src.core.validation import (
    run_synthetic_test as _run_synthetic_test,
)
from src.core.validation import (
    validate_rollback_completion as _validate_rollback_completion,
)
from src.core.validation import (
    verify_alert_resolution as _verify_alert_resolution,
)

logger = get_logger(__name__)
settings = get_settings()


class ValidationResult(BaseModel):
    """Result of a single validation check (health, metric, synthetic, compliance, or baseline)."""

    check_id: str
    check_type: str  # health, metric, log, synthetic, compliance
    target: str
    passed: bool
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    severity: str = "info"  # info, warning, critical
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ValidationReport(BaseModel):
    """Aggregated validation report with pass/fail status per check and overall recommendations."""

    incident_id: UUID
    validation_id: UUID
    overall_status: str  # passed, failed, partial
    passed_checks: int = 0
    failed_checks: int = 0
    warning_checks: int = 0
    total_checks: int = 0
    checks: list[ValidationResult] = Field(default_factory=list)
    summary: str = ""
    recommendations: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ValidatorState(BaseAgentState):
    """State for the validator agent, tracking execution context and required check types."""

    incident: Incident | None = None
    execution_id: UUID | None = None
    validation_report: ValidationReport | None = None
    validation_config: dict[str, Any] = Field(default_factory=dict)
    required_checks: list[str] = Field(default_factory=list)


class ValidatorAgent(ReactAgent):
    """Agent that validates remediation actions and incident resolutions."""

    def _get_specific_prompt(self) -> str:
        return """You are the Validator Agent responsible for verifying that remediation actions
have successfully resolved incidents and that systems are healthy.

Your responsibilities:
1. Execute validation checks after remediation actions
2. Verify system health metrics have returned to normal
3. Run synthetic transactions to verify functionality
4. Check compliance with SLAs and policies
5. Validate no regressions were introduced
6. Confirm incident can be safely closed
7. Generate comprehensive validation reports

Available tools:
- check_service_health: Verify service health endpoints
- query_metrics: Compare metrics before/after remediation
- run_synthetic_test: Execute synthetic transactions
- verify_alert_resolution: Confirm alerts have resolved
- check_compliance: Verify policy compliance
- compare_baselines: Compare current state to baselines
- validate_rollback: Verify rollback completed successfully

Output: Structured ValidationReport with pass/fail status and recommendations."""

    def _get_tools(self) -> list[BaseTool]:
        return [
            check_service_health,
            query_metrics,
            run_synthetic_test,
            verify_alert_resolution,
            check_compliance,
            compare_baselines,
            validate_rollback,
        ]

    def _get_state_class(self) -> type[BaseAgentState]:
        return ValidatorState

    async def _process_task(self, state: ValidatorState) -> ValidatorState:
        """Process validation task."""
        task = state.task
        if not task:
            state.error = "No task provided"
            state.should_continue = False
            return state

        # Get incident and execution info
        incident_id = task.context.get("incident_id") or task.input_data.get("incident_id")
        execution_id = task.context.get("execution_id") or task.input_data.get("execution_id")

        if incident_id:
            state.incident = await self._get_incident(incident_id)
        if execution_id:
            state.execution_id = execution_id

        if not state.incident:
            state.error = "No incident found for validation"
            state.should_continue = False
            return state

        # Get validation config
        state.validation_config = task.input_data.get("validation_config", {})
        state.required_checks = state.validation_config.get("required_checks", [
            "health_endpoint",
            "key_metrics",
            "synthetic_transaction",
            "alert_resolution",
            "compliance",
        ])

        # Run validation
        report = await self._run_validation(state)
        state.validation_report = report
        state.intermediate_results["validation_report"] = report.model_dump()

        # Determine if validation passed
        if report.overall_status == "passed":
            state.should_continue = False
        else:
            state.should_continue = False  # Could retry with different config

        return state

    async def _run_validation(self, state: ValidatorState) -> ValidationReport:
        """Run all configured validation checks and produce a report."""
        incident = state.incident
        checks = []

        # 1. Health endpoint checks
        if "health_endpoint" in state.required_checks:
            for service in incident.affected_services:
                result = await check_service_health.ainvoke({"service_name": service})
                checks.append(ValidationResult(
                    check_id=f"health_{service}",
                    check_type="health",
                    target=service,
                    passed=result.get("healthy", False),
                    message=result.get("message", ""),
                    details=result,
                    severity="critical" if not result.get("healthy") else "info",
                ))

        # 2. Key metrics validation
        if "key_metrics" in state.required_checks:
            for resource in incident.affected_resources:
                result = await query_metrics.ainvoke({
                    "resource_id": resource,
                    "compare_to_baseline": True,
                })
                passed = result.get("within_baseline", False)
                checks.append(ValidationResult(
                    check_id=f"metrics_{resource}",
                    check_type="metric",
                    target=resource,
                    passed=passed,
                    message=result.get("summary", ""),
                    details=result,
                    severity="warning" if not passed else "info",
                ))

        # 3. Synthetic transactions
        if "synthetic_transaction" in state.required_checks:
            for service in incident.affected_services:
                result = await run_synthetic_test.ainvoke({
                    "service_name": service,
                    "test_type": "smoke",
                })
                checks.append(ValidationResult(
                    check_id=f"synthetic_{service}",
                    check_type="synthetic",
                    target=service,
                    passed=result.get("passed", False),
                    message=result.get("message", ""),
                    details=result,
                    severity="critical" if not result.get("passed") else "info",
                ))

        # 4. Alert resolution verification
        if "alert_resolution" in state.required_checks:
            result = await verify_alert_resolution.ainvoke({
                "incident_id": str(incident.id),
                "resource_ids": incident.affected_resources,
            })
            checks.append(ValidationResult(
                check_id="alert_resolution",
                check_type="alert",
                target="incident_alerts",
                passed=result.get("all_resolved", False),
                message=result.get("summary", ""),
                details=result,
                severity="warning" if not result.get("all_resolved") else "info",
            ))

        # 5. Compliance check
        if "compliance" in state.required_checks:
            result = await check_compliance.ainvoke({
                "incident_id": str(incident.id),
                "execution_id": str(state.execution_id) if state.execution_id else None,
            })
            checks.append(ValidationResult(
                check_id="compliance",
                check_type="compliance",
                target="incident_process",
                passed=result.get("compliant", False),
                message=result.get("summary", ""),
                details=result,
                severity="warning" if not result.get("compliant") else "info",
            ))

        # 6. Baseline comparison
        if "baseline_comparison" in state.required_checks:
            result = await compare_baselines.ainvoke({
                "resource_ids": incident.affected_resources,
            })
            passed = result.get("all_within_baseline", False)
            checks.append(ValidationResult(
                check_id="baseline_comparison",
                check_type="baseline",
                target="affected_resources",
                passed=passed,
                message=result.get("summary", ""),
                details=result,
                severity="warning" if not passed else "info",
            ))

        # Calculate summary
        passed = sum(1 for c in checks if c.passed)
        failed = sum(1 for c in checks if not c.passed and c.severity == "critical")
        warnings = sum(1 for c in checks if not c.passed and c.severity == "warning")

        overall_status = "passed" if failed == 0 else "failed"

        # Generate recommendations
        recommendations = []
        for check in checks:
            if not check.passed:
                if check.severity == "critical":
                    recommendations.append(f"CRITICAL: {check.target} - {check.message}")
                else:
                    recommendations.append(f"WARNING: {check.target} - {check.message}")

        return ValidationReport(
            incident_id=incident.id,
            validation_id=uuid4(),
            overall_status=overall_status,
            passed_checks=passed,
            failed_checks=failed,
            warning_checks=warnings,
            total_checks=len(checks),
            checks=checks,
            summary=(
                f"Validation {'PASSED' if overall_status == 'passed' else 'FAILED'}: "
                f"{passed}/{len(checks)} checks passed"
            ),
            recommendations=recommendations,
        )


# Tools for Validator Agent
@tool
async def check_service_health(service_name: str) -> dict[str, Any]:
    """Check service health endpoint."""
    logger.info("Checking service health", service=service_name)
    result = await check_http_health(f"http://{service_name}/health")
    return {"healthy": result["healthy"], "message": result["message"], "endpoint": f"https://{service_name}/health"}


@tool
async def query_metrics(
    resource_id: str,
    compare_to_baseline: bool = True,
) -> dict[str, Any]:
    """Query and validate metrics against baseline."""
    logger.info("Querying metrics", resource=resource_id, compare=compare_to_baseline)
    result = await query_metrics_for_resource(resource_id)
    within_baseline = result.get("status") == "healthy"
    return {
        "within_baseline": within_baseline,
        "summary": result.get("summary", ""),
        "details": result.get("metrics", {}),
    }


@tool
async def run_synthetic_test(
    service_name: str,
    test_type: str = "smoke",
) -> dict[str, Any]:
    """Run synthetic transaction test."""
    logger.info("Running synthetic test", service=service_name, test_type=test_type)
    return await _run_synthetic_test(service_name, test_type)


@tool
async def verify_alert_resolution(
    incident_id: str,
    resource_ids: list[str],
) -> dict[str, Any]:
    """Verify all related alerts have resolved."""
    logger.info("Verifying alert resolution", incident_id=incident_id)
    return await _verify_alert_resolution(incident_id, resource_ids)


@tool
async def check_compliance(
    incident_id: str,
    execution_id: str | None = None,
) -> dict[str, Any]:
    """Check compliance with policies and SLAs."""
    logger.info("Checking compliance", incident_id=incident_id)
    return await _check_incident_compliance(incident_id, execution_id)


@tool
async def compare_baselines(
    resource_ids: list[str],
) -> dict[str, Any]:
    """Compare current state to established baselines."""
    logger.info("Comparing baselines", resources=resource_ids)
    return await _compare_resource_baselines(resource_ids)


@tool
async def validate_rollback(
    execution_id: str,
) -> dict[str, Any]:
    """Validate that rollback completed successfully."""
    logger.info("Validating rollback", execution_id=execution_id)
    return await _validate_rollback_completion(execution_id)


# Export
__all__ = [
    "ValidationReport",
    "ValidationResult",
    "ValidatorAgent",
    "ValidatorState",
]
