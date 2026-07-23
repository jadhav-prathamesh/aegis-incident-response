"""Tests for the action dispatcher."""

import unittest

from src.core.action_dispatcher import dispatch_action


class ActionDispatcherTests(unittest.IsolatedAsyncioTestCase):
    """Unit tests for action dispatching."""

    async def test_unknown_action_type(self) -> None:
        result = await dispatch_action(
            action_type="UNKNOWN_ACTION",
            target_resource="test",
            target_resource_type="VM",
            parameters={},
        )
        self.assertFalse(result["success"])
        self.assertIn("Unknown action type", result["error"])

    async def test_dry_run_returns_dry_run_flag(self) -> None:
        result = await dispatch_action(
            action_type="RESTART_SERVICE",
            target_resource="api-server",
            target_resource_type="CONTAINER",
            parameters={"namespace": "default"},
            dry_run=True,
        )
        self.assertTrue(result["success"])
        self.assertTrue(result["output"].get("dry_run"))

    async def test_create_ticket(self) -> None:
        result = await dispatch_action(
            action_type="CREATE_TICKET",
            target_resource="web-server",
            target_resource_type="VM",
            parameters={"title": "Test ticket"},
        )
        self.assertTrue(result["success"])
        self.assertIn("ticket_number", result["output"])

    async def test_notify_oncall(self) -> None:
        result = await dispatch_action(
            action_type="NOTIFY_ONCALL",
            target_resource="api",
            target_resource_type="CONTAINER",
            parameters={"channel": "slack", "message": "Test"},
        )
        self.assertTrue(result["success"])
        self.assertTrue(result["output"].get("notified"))

    async def test_escalate(self) -> None:
        result = await dispatch_action(
            action_type="ESCALATE",
            target_resource="db-primary",
            target_resource_type="DATABASE",
            parameters={"reason": "Test escalation"},
        )
        self.assertTrue(result["success"])
        self.assertTrue(result["output"].get("escalated"))

    async def test_failover(self) -> None:
        result = await dispatch_action(
            action_type="FAILOVER",
            target_resource="lb-primary",
            target_resource_type="LOAD_BALANCER",
            parameters={"standby_target": "lb-secondary"},
        )
        self.assertTrue(result["success"])
        self.assertIn("Failover initiated", result["output"]["message"])

    async def test_clear_cache(self) -> None:
        result = await dispatch_action(
            action_type="CLEAR_CACHE",
            target_resource="redis-cache",
            target_resource_type="CACHE",
            parameters={"host": "localhost", "port": 9999, "pattern": "*"},
        )
        self.assertTrue(result["success"])

    async def test_run_diagnostic(self) -> None:
        result = await dispatch_action(
            action_type="RUN_DIAGNOSTIC",
            target_resource="test-host",
            target_resource_type="VM",
            parameters={"commands": ["echo hello"]},
        )
        self.assertTrue(result["success"])
        self.assertIn("diagnostics", result["output"])


if __name__ == "__main__":
    unittest.main()
