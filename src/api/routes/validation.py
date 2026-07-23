"""Validation endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.core.validation import (
    check_incident_compliance,
    compare_resource_baselines,
    run_synthetic_test,
    validate_rollback_completion,
    verify_alert_resolution,
)

router = APIRouter()


class SyntheticTestRequest(BaseModel):
    """Request to run a synthetic test against a service."""

    service_name: str
    test_type: str = "smoke"
    endpoint: str | None = None


class AlertVerifyRequest(BaseModel):
    """Request to verify alert resolution for an incident."""

    incident_id: str
    resource_ids: list[str] = Field(default_factory=list)


class ComplianceRequest(BaseModel):
    """Request to run compliance checks for an incident."""

    incident_id: str
    execution_id: str | None = None


class BaselineRequest(BaseModel):
    """Request to compare resource metrics against baselines."""

    resource_ids: list[str] = Field(default_factory=list)


class RollbackValidateRequest(BaseModel):
    """Request to validate a rollback operation."""

    execution_id: str
    service_name: str | None = None


@router.post("/synthetic")
async def synthetic_test(req: SyntheticTestRequest) -> dict[str, Any]:
    """Run a synthetic test against a service."""
    return await run_synthetic_test(req.service_name, req.test_type, req.endpoint)


@router.post("/alerts")
async def verify_alerts(req: AlertVerifyRequest) -> dict[str, Any]:
    """Verify alert resolution for an incident."""
    return await verify_alert_resolution(req.incident_id, req.resource_ids)


@router.post("/compliance")
async def compliance_check(req: ComplianceRequest) -> dict[str, Any]:
    """Run compliance checks."""
    return await check_incident_compliance(req.incident_id, req.execution_id)


@router.post("/baselines")
async def baseline_check(req: BaselineRequest) -> dict[str, Any]:
    """Compare resources against baselines."""
    return await compare_resource_baselines(req.resource_ids)


@router.post("/rollback")
async def rollback_validate(req: RollbackValidateRequest) -> dict[str, Any]:
    """Validate a rollback operation."""
    return await validate_rollback_completion(req.execution_id, req.service_name)
