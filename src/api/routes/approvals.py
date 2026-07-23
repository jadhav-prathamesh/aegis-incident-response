"""Approval management endpoints."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.core.approval import (
    approve_request,
    create_approval_request,
    get_approval_request,
    list_pending_approvals,
    reject_request,
)

router = APIRouter()


class ApprovalCreateRequest(BaseModel):
    """Request to create a new approval."""

    action_type: str
    target_resource: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    incident_id: str | None = None
    execution_id: str | None = None


class ApprovalActionRequest(BaseModel):
    """Request body for approving a request."""

    approver: str = "api-user"
    notes: str = ""


class ApprovalRejectRequest(BaseModel):
    """Request body for rejecting a request."""

    rejector: str = "api-user"
    reason: str = "Rejected via API"


class ApprovalResponse(BaseModel):
    """Approval request response schema."""

    id: str
    action_type: str
    target_resource: str
    status: str
    created_at: str
    resolved_at: str | None = None
    resolved_by: str | None = None
    rejection_reason: str | None = None


def _approval_to_response(req: Any) -> ApprovalResponse:
    """Convert an ApprovalRequest domain object to the API response schema."""
    return ApprovalResponse(
        id=str(req.id),
        action_type=req.action_type,
        target_resource=req.target_resource,
        status=req.status.value,
        created_at=req.created_at.isoformat(),
        resolved_at=req.resolved_at.isoformat() if req.resolved_at else None,
        resolved_by=req.resolved_by,
        rejection_reason=req.rejection_reason,
    )


@router.get("/pending", response_model=list[ApprovalResponse])
async def get_pending_approvals() -> list[ApprovalResponse]:
    """List pending approval requests."""
    return [_approval_to_response(r) for r in list_pending_approvals()]


@router.post("", response_model=ApprovalResponse, status_code=201)
async def create_approval(req: ApprovalCreateRequest) -> ApprovalResponse:
    """Create a new approval request."""
    request = create_approval_request(
        action_type=req.action_type,
        target_resource=req.target_resource,
        parameters=req.parameters,
        incident_id=req.incident_id,
        execution_id=req.execution_id,
    )
    return _approval_to_response(request)


@router.post("/{approval_id}/approve", response_model=ApprovalResponse)
async def approve(approval_id: UUID, req: ApprovalActionRequest) -> ApprovalResponse:
    """Approve a pending request."""
    result = approve_request(approval_id, approver=req.approver, notes=req.notes)
    if result is None:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return _approval_to_response(result)


@router.post("/{approval_id}/reject", response_model=ApprovalResponse)
async def reject(approval_id: UUID, req: ApprovalRejectRequest) -> ApprovalResponse:
    """Reject a pending request."""
    result = reject_request(approval_id, reason=req.reason, rejector=req.rejector)
    if result is None:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return _approval_to_response(result)


@router.get("/{approval_id}", response_model=ApprovalResponse)
async def get_approval(approval_id: UUID) -> ApprovalResponse:
    """Retrieve an approval request by ID."""
    result = get_approval_request(approval_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return _approval_to_response(result)
