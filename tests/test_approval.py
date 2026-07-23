"""Tests for the approval workflow."""

import unittest

from src.core.approval import (
    ApprovalStatus,
    approve_request,
    create_approval_request,
    get_approval_request,
    list_pending_approvals,
    reject_request,
    requires_approval,
)


class ApprovalWorkflowTests(unittest.TestCase):
    """Unit tests for approval workflow."""

    def test_create_auto_approved_in_dev(self) -> None:
        req = create_approval_request(
            action_type="RESTART_SERVICE",
            target_resource="api-server",
            parameters={"namespace": "default"},
        )
        self.assertEqual(req.status, ApprovalStatus.APPROVED)
        self.assertIsNotNone(req.resolved_at)

    def test_get_approval_request(self) -> None:
        req = create_approval_request(
            action_type="SCALE_UP",
            target_resource="deployment/web",
            parameters={"replicas": 5},
        )
        found = get_approval_request(req.id)
        self.assertIsNotNone(found)
        self.assertEqual(found.id, req.id)

    def test_approve_request(self) -> None:
        req = create_approval_request(
            action_type="ROLLBACK_DEPLOYMENT",
            target_resource="deployment/api",
            parameters={},
            auto_approve_in_dev=False,
        )
        self.assertEqual(req.status, ApprovalStatus.PENDING)

        approved = approve_request(req.id, approver="sre-team", notes="Looks safe")
        self.assertIsNotNone(approved)
        self.assertEqual(approved.status, ApprovalStatus.APPROVED)
        self.assertEqual(approved.resolved_by, "sre-team")

    def test_reject_request(self) -> None:
        req = create_approval_request(
            action_type="ISOLATE_HOST",
            target_resource="db-primary",
            parameters={},
            auto_approve_in_dev=False,
        )
        rejected = reject_request(req.id, reason="Too risky", rejector="security")
        self.assertIsNotNone(rejected)
        self.assertEqual(rejected.status, ApprovalStatus.REJECTED)
        self.assertEqual(rejected.rejection_reason, "Too risky")

    def test_list_pending_approvals(self) -> None:
        create_approval_request(
            action_type="FLUSH_QUEUE",
            target_resource="queue/orders",
            parameters={},
            auto_approve_in_dev=False,
        )
        pending = list_pending_approvals()
        self.assertTrue(any(r.action_type == "FLUSH_QUEUE" for r in pending))

    def test_requires_approval_logic(self) -> None:
        self.assertTrue(requires_approval("ISOLATE_HOST", "HIGH"))
        self.assertTrue(requires_approval("FLUSH_QUEUE", "LOW"))
        self.assertTrue(requires_approval("CUSTOM_SCRIPT", "MEDIUM"))
        self.assertFalse(requires_approval("RUN_DIAGNOSTIC", "LOW"))


if __name__ == "__main__":
    unittest.main()
