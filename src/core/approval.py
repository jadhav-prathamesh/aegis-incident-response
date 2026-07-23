"""Approval workflow for high-risk remediation actions."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class ApprovalStatus(StrEnum):
    """Possible states of an approval request."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    TIMED_OUT = "TIMED_OUT"


class ApprovalRequest:
    """An approval request for a high-risk action."""

    def __init__(
        self,
        action_type: str,
        target_resource: str,
        parameters: dict[str, Any],
        incident_id: str | None = None,
        execution_id: str | None = None,
        requested_by: str = "executor_agent",
        timeout_minutes: int | None = None,
    ):
        self.id: UUID = uuid4()
        self.action_type = action_type
        self.target_resource = target_resource
        self.parameters = parameters
        self.incident_id = incident_id
        self.execution_id = execution_id
        self.requested_by = requested_by
        self.status: ApprovalStatus = ApprovalStatus.PENDING
        self.created_at: datetime = datetime.now(UTC)
        self.timeout_minutes = timeout_minutes or settings.agent.default_timeout // 60
        self.resolved_at: datetime | None = None
        self.resolved_by: str | None = None
        self.rejection_reason: str | None = None
        self.notes: list[dict[str, Any]] = []

    @property
    def is_expired(self) -> bool:
        """Check if this request has exceeded its timeout."""
        if self.status != ApprovalStatus.PENDING:
            return False
        expiry = self.created_at + timedelta(minutes=self.timeout_minutes)
        return datetime.now(UTC) > expiry

    def approve(self, approver: str = "system", notes: str = "") -> None:
        """Mark this request as approved."""
        self.status = ApprovalStatus.APPROVED
        self.resolved_at = datetime.now(UTC)
        self.resolved_by = approver
        if notes:
            self.notes.append({
                "author": approver,
                "content": notes,
                "timestamp": self.resolved_at.isoformat(),
            })

    def reject(self, reason: str, rejector: str = "system") -> None:
        """Mark this request as rejected."""
        self.status = ApprovalStatus.REJECTED
        self.resolved_at = datetime.now(UTC)
        self.resolved_by = rejector
        self.rejection_reason = reason
        self.notes.append({
            "author": rejector,
            "content": f"Rejected: {reason}",
            "timestamp": self.resolved_at.isoformat(),
        })

    def timeout(self) -> None:
        """Mark this request as timed out."""
        self.status = ApprovalStatus.TIMED_OUT
        self.resolved_at = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return {
            "id": str(self.id),
            "action_type": self.action_type,
            "target_resource": self.target_resource,
            "parameters": self.parameters,
            "incident_id": self.incident_id,
            "execution_id": self.execution_id,
            "requested_by": self.requested_by,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
            "rejection_reason": self.rejection_reason,
            "notes": self.notes,
            "is_expired": self.is_expired,
        }


# In-memory approval store
_pending_approvals: dict[UUID, ApprovalRequest] = {}
_approval_history: list[ApprovalRequest] = []


def create_approval_request(
    action_type: str,
    target_resource: str,
    parameters: dict[str, Any],
    incident_id: str | None = None,
    execution_id: str | None = None,
    auto_approve_in_dev: bool = True,
) -> ApprovalRequest:
    """Create a new approval request.

    In development environments with auto_approve_in_dev=True, the request is
    auto-approved so the workflow can continue without manual intervention.
    """
    request = ApprovalRequest(
        action_type=action_type,
        target_resource=target_resource,
        parameters=parameters,
        incident_id=incident_id,
        execution_id=execution_id,
    )

    is_dev = getattr(settings, "environment", "development") == "development"
    if is_dev and auto_approve_in_dev:
        request.approve(approver="auto-approver", notes="Auto-approved in development environment")
        logger.info(
            "Approval auto-approved (dev mode)",
            approval_id=str(request.id),
            action_type=action_type,
        )
    else:
        _pending_approvals[request.id] = request
        logger.info(
            "Approval request created",
            approval_id=str(request.id),
            action_type=action_type,
            target=target_resource,
        )

    _approval_history.append(request)
    return request


def get_approval_request(approval_id: UUID) -> ApprovalRequest | None:
    """Retrieve an approval request by ID."""
    if approval_id in _pending_approvals:
        return _pending_approvals[approval_id]
    for req in _approval_history:
        if req.id == approval_id:
            return req
    return None


def list_pending_approvals() -> list[ApprovalRequest]:
    """List all pending approval requests."""
    expired = [r for r in _pending_approvals.values() if r.is_expired]
    for req in expired:
        req.timeout()
        _pending_approvals.pop(req.id, None)

    return list(_pending_approvals.values())


def approve_request(
    approval_id: UUID,
    approver: str = "manual",
    notes: str = "",
) -> ApprovalRequest | None:
    """Approve a pending request."""
    request = _pending_approvals.pop(approval_id, None)
    if request is None:
        return None

    request.approve(approver=approver, notes=notes)
    _approval_history.append(request)
    logger.info("Approval granted", approval_id=str(approval_id), approver=approver)
    return request


def reject_request(
    approval_id: UUID,
    reason: str,
    rejector: str = "manual",
) -> ApprovalRequest | None:
    """Reject a pending request."""
    request = _pending_approvals.pop(approval_id, None)
    if request is None:
        return None

    request.reject(reason=reason, rejector=rejector)
    _approval_history.append(request)
    logger.info("Approval rejected", approval_id=str(approval_id), rejector=rejector, reason=reason)
    return request


def requires_approval(action_type: str, risk_level: str = "LOW") -> bool:
    """Determine whether an action requires human approval."""
    always_require = {
        "RESTART_SERVICE",
        "ROLLBACK_DEPLOYMENT",
        "FAILOVER",
        "ISOLATE_HOST",
        "BLOCK_IP",
        "CUSTOM_SCRIPT",
        "SCALE_DOWN",
        "FLUSH_QUEUE",
    }

    if action_type in always_require:
        return True
    return risk_level == "CRITICAL"
