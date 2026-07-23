"""Tests for the REST API endpoints."""

import unittest
from uuid import uuid4

from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.api.app import app
from src.core.incident_store import save_incident
from src.core.models import (
    Incident,
    IncidentCategory,
    IncidentSeverity,
    IncidentStatus,
)


class HealthEndpointTests(unittest.TestCase):
    def test_health(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "healthy")

    def test_info(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/info")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("version", resp.json())


class IncidentEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_list_incidents(self) -> None:
        resp = self.client.get("/api/v1/incidents")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), list)

    def test_create_incident(self) -> None:
        payload = {
            "title": "Test incident",
            "description": "A test incident for API validation",
            "severity": "SEV3",
            "category": "APPLICATION",
            "source": "test",
            "affected_services": ["api-server"],
        }
        resp = self.client.post("/api/v1/incidents", json=payload)
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data["title"], "Test incident")
        self.assertEqual(data["severity"], "SEV3")

    def test_get_incident_not_found(self) -> None:
        resp = self.client.get(f"/api/v1/incidents/{uuid4()}")
        self.assertEqual(resp.status_code, 404)

    def test_get_incident(self) -> None:
        inc = Incident(
            title="Fetchable incident",
            description="Can be fetched",
            severity=IncidentSeverity.SEV2,
            status=IncidentStatus.OPEN,
            category=IncidentCategory.INFRASTRUCTURE,
            source="test",
        )
        saved = save_incident(inc)
        resp = self.client.get(f"/api/v1/incidents/{saved.id}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["title"], "Fetchable incident")

    def test_update_incident(self) -> None:
        inc = Incident(
            title="Updatable incident",
            description="Can be updated",
            severity=IncidentSeverity.SEV3,
            status=IncidentStatus.OPEN,
            category=IncidentCategory.APPLICATION,
            source="test",
        )
        saved = save_incident(inc)
        resp = self.client.patch(
            f"/api/v1/incidents/{saved.id}",
            json={"status": "RESOLVED", "root_cause": "Fixed it"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "RESOLVED")
        self.assertEqual(resp.json()["root_cause"], "Fixed it")


class ApprovalEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_list_pending_approvals(self) -> None:
        resp = self.client.get("/api/v1/approvals/pending")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), list)

    def test_create_approval(self) -> None:
        payload = {
            "action_type": "RESTART_SERVICE",
            "target_resource": "api-server",
            "parameters": {},
        }
        resp = self.client.post("/api/v1/approvals", json=payload)
        self.assertEqual(resp.status_code, 201)
        self.assertIn("id", resp.json())


class AgentEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_list_agent_types(self) -> None:
        resp = self.client.get("/api/v1/agents/types")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("PLANNER", resp.json())

    def test_execute_invalid_agent_type_returns_400(self) -> None:
        resp = self.client.post(
            "/api/v1/agents/execute",
            json={
                "agent_type": "RCA_ANALYZER",
                "task_type": "test",
                "input_data": {},
            },
        )
        self.assertEqual(resp.status_code, 400)


class ExceptionChainingTests(unittest.TestCase):
    """Exception chaining with `from exc` preserves original traceback."""

    def test_value_error_from_get_agent_has_cause_chain(self) -> None:
        from src.agents.base import get_agent
        from src.core.models import AgentType

        with self.assertRaises(HTTPException) as ctx:
            try:
                get_agent(AgentType("UNKNOWN"))
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc

        self.assertIsNotNone(ctx.exception.__cause__)
        self.assertIsInstance(ctx.exception.__cause__, ValueError)


if __name__ == "__main__":
    unittest.main()
