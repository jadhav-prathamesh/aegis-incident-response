"""Behavioural tests for pipeline agents: Observer, Executor, Validator, Planner."""

from datetime import UTC, datetime
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.agents.executor import ExecutorAgent, ExecutorState
from src.agents.observer import ObservationResult, ObserverAgent, ObserverState
from src.agents.planner import PlannerAgent, PlannerState
from src.agents.validator import ValidatorAgent, ValidatorState
from src.core.models import (
    AgentConfig,
    AgentTask,
    AgentType,
    Alert,
    Incident,
    IncidentCategory,
    IncidentSeverity,
    IncidentStatus,
    ResourceType,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BOB_ID = uuid4()


def _make_incident(
    sev: IncidentSeverity = IncidentSeverity.SEV3,
    services: list[str] | None = None,
    resources: list[str] | None = None,
) -> Incident:
    return Incident(
        id=_BOB_ID,
        title="test incident",
        description="behavioural test incident",
        severity=sev,
        status=IncidentStatus.OPEN,
        category=IncidentCategory.APPLICATION,
        source="test",
        affected_services=services or ["svc-a"],
        affected_resources=resources or ["res-1"],
    )


def _observation_result(
    status: str = "healthy",
    check_type: str = "health",
    target: str = "svc-a",
) -> ObservationResult:
    return ObservationResult(
        check_id=f"{check_type}_{target}",
        check_type=check_type,
        target=target,
        status=status,
        message="OK" if status == "healthy" else f"{status} condition",
    )


def _alert(sev: IncidentSeverity = IncidentSeverity.SEV5) -> dict[str, object]:
    """Create a mock alert dict matching get_active_alerts_for_resources return type."""
    return {
        "alert_name": "test-alert",
        "severity": sev.value,
        "status": "firing",
        "source": "prometheus",
        "source_id": "prom-1",
        "message": f"{sev.value} alert",
        "starts_at": "",
        "resources": [],
    }


# ---------------------------------------------------------------------------
# Observer Agent
# ---------------------------------------------------------------------------


class ObserverLogicTests(IsolatedAsyncioTestCase):
    """Pure-method tests for Observer status/recommendation logic."""

    def setUp(self) -> None:
        self.agent = ObserverAgent(config=AgentConfig(agent_type=AgentType.OBSERVER))

    # -- _determine_overall_status --

    def test_status_critical_when_critical_alert_exists(self) -> None:
        checks = [_observation_result("healthy")]
        alerts = [_alert(IncidentSeverity.SEV1)]
        self.assertEqual(self.agent._determine_overall_status(checks, alerts), "critical")

    def test_status_critical_when_many_unhealthy(self) -> None:
        checks = [_observation_result("unhealthy", target=f"svc-{i}") for i in range(3)]
        status = self.agent._determine_overall_status(checks, [])
        self.assertEqual(status, "critical")

    def test_status_degrading_when_some_unhealthy(self) -> None:
        checks = [_observation_result("unhealthy", target="svc-1")]
        status = self.agent._determine_overall_status(checks, [])
        self.assertEqual(status, "degrading")

    def test_status_degrading_when_many_degraded(self) -> None:
        checks = [_observation_result("degraded", target=f"svc-{i}") for i in range(3)]
        status = self.agent._determine_overall_status(checks, [])
        self.assertEqual(status, "degrading")

    def test_status_degraded_when_few_degraded(self) -> None:
        checks = [_observation_result("degraded", target="svc-1")]
        status = self.agent._determine_overall_status(checks, [])
        self.assertEqual(status, "degraded")

    def test_status_stable_when_all_healthy(self) -> None:
        checks = [
            _observation_result("healthy", target=f"svc-{i}") for i in range(3)
        ]
        status = self.agent._determine_overall_status(checks, [])
        self.assertEqual(status, "stable")

    # -- _generate_recommendations --

    def test_recommendations_includes_unhealthy_checks(self) -> None:
        checks = [_observation_result("unhealthy", target="svc-db")]
        recs = self.agent._generate_recommendations(checks, [], _make_incident())
        self.assertTrue(any("Investigate svc-db" in r for r in recs))

    def test_recommendations_includes_degraded_checks(self) -> None:
        checks = [_observation_result("degraded", target="svc-cache")]
        recs = self.agent._generate_recommendations(checks, [], _make_incident())
        self.assertTrue(any("Monitor svc-cache" in r for r in recs))

    def test_recommendations_includes_critical_alerts(self) -> None:
        alerts = [_alert(IncidentSeverity.SEV1)]
        recs = self.agent._generate_recommendations([], alerts, _make_incident())
        self.assertTrue(any("Critical alert" in r for r in recs))

    def test_recommendations_high_severity_incident(self) -> None:
        inc = _make_incident(sev=IncidentSeverity.SEV1)
        recs = self.agent._generate_recommendations([], [], inc)
        self.assertTrue(any("on-call" in r.lower() for r in recs))

    def test_recommendations_limited_to_10(self) -> None:
        checks = [_observation_result("unhealthy", target=f"svc-{i}") for i in range(15)]
        recs = self.agent._generate_recommendations(checks, [], _make_incident())
        self.assertLessEqual(len(recs), 10)

    def test_recommendations_empty_when_healthy(self) -> None:
        checks = [_observation_result("healthy", target="svc-1")]
        recs = self.agent._generate_recommendations(checks, [], _make_incident())
        self.assertEqual(recs, [])

    # -- _summarize_metrics --

    def test_summarize_metrics_counts(self) -> None:
        checks = [
            _observation_result("healthy", check_type="metric", target="res-1"),
            _observation_result("degraded", check_type="metric", target="res-2"),
            _observation_result("unhealthy", check_type="metric", target="res-3"),
            _observation_result("healthy", check_type="health", target="svc-1"),
        ]
        summary = self.agent._summarize_metrics(checks)
        self.assertEqual(summary["total_checks"], 3)
        self.assertEqual(summary["healthy"], 1)
        self.assertEqual(summary["degraded"], 1)
        self.assertEqual(summary["unhealthy"], 1)


class ObserverProcessTaskTests(IsolatedAsyncioTestCase):
    """Observer._process_task with mocked tools."""

    def setUp(self) -> None:
        self.agent = ObserverAgent(config=AgentConfig(agent_type=AgentType.OBSERVER))

    async def test_no_task_sets_error(self) -> None:
        state = ObserverState()
        result = await self.agent._process_task(state)
        self.assertIsNotNone(result.error)

    async def test_process_task_with_mocked_tools(self) -> None:
        state = ObserverState()
        state.task = AgentTask(
            agent_type=AgentType.OBSERVER,
            task_type="observe",
            input_data={},
        )
        state.incident = _make_incident(
            services=["web-api", "db-primary"],
            resources=["web-1", "db-1"],
        )

        health_result = {"healthy": True, "status_code": 200, "message": "OK"}
        metrics_result = {"status": "healthy", "summary": "all good", "metrics": {}}
        alerts_result: list[dict] = []
        logs_result = {
            "status": "healthy", "summary": "no anomalies",
            "resources_checked": [], "patterns_monitored": [],
            "since_minutes": 60, "anomalies": [],
        }

        with patch("src.agents.observer.check_http_health", AsyncMock(return_value=health_result)), \
             patch("src.agents.observer.query_metrics_for_resource", AsyncMock(return_value=metrics_result)), \
             patch("src.agents.observer.get_active_alerts_for_resources", AsyncMock(return_value=alerts_result)), \
             patch("src.agents.observer.analyze_logs_simple", AsyncMock(return_value=logs_result)):
            result = await self.agent._process_task(state)

        self.assertIsNone(result.error)
        self.assertIsNotNone(result.observation)
        self.assertEqual(result.observation.overall_status, "stable")
        # 2 services (health) + 2 resources (metrics + deps) + 1 log = 7
        self.assertEqual(len(result.observation.checks), 7)
        self.assertFalse(result.should_continue)  # stable -> no re-observe


# ---------------------------------------------------------------------------
# Executor Agent
# ---------------------------------------------------------------------------


class ExecutorProcessTaskTests(IsolatedAsyncioTestCase):
    """Executor step execution, approval, and rollback flows."""

    def setUp(self) -> None:
        self.agent = ExecutorAgent(config=AgentConfig(agent_type=AgentType.EXECUTOR))

    async def test_no_task_sets_error(self) -> None:
        state = ExecutorState()
        result = await self.agent._process_task(state)
        self.assertIsNotNone(result.error)

    async def test_missing_incident_or_plan_errors(self) -> None:
        state = ExecutorState()
        state.task = AgentTask(
            agent_type=AgentType.EXECUTOR,
            task_type="execute",
            input_data={},
        )
        result = await self.agent._process_task(state)
        self.assertIn("Missing", result.error or "")

    async def _run_executor(
        self,
        steps: list[dict],
        tool_mocks: dict[str, dict],
    ) -> ExecutorState:
        state = ExecutorState()
        state.task = AgentTask(
            agent_type=AgentType.EXECUTOR,
            task_type="execute",
            input_data={"plan": {"plan_id": "p-1", "steps": steps}},
        )
        state.incident = _make_incident()

        patchers: list[patch] = []

        dispatch_ret = tool_mocks.get("dispatch_action", {"success": True})
        patchers.append(
            patch("src.agents.executor.dispatch_action", new=AsyncMock(return_value=dispatch_ret))
        )

        if "create_approval_request" in tool_mocks:
            req_mock = MagicMock()
            req_mock.status.value = tool_mocks["create_approval_request"]
            req_mock.id = uuid4()
            patchers.append(
                patch("src.core.approval.create_approval_request", new=MagicMock(return_value=req_mock))
            )

        if "initiate_rollback" in tool_mocks:
            rollback_tool = MagicMock()
            rollback_tool.ainvoke = AsyncMock(return_value=tool_mocks["initiate_rollback"])
            patchers.append(patch("src.agents.executor.initiate_rollback", new=rollback_tool))

        for p in patchers:
            p.start()
        try:
            return await self.agent._process_task(state)
        finally:
            for p in patchers:
                p.stop()

    async def test_single_step_success(self) -> None:
        steps = [{
            "step_id": "s1", "action_type": "restart",
            "target_resource": "web-1",
            "target_resource_type": ResourceType.CONTAINER,
            "parameters": {}, "requires_approval": False,
            "description": "restart web container",
        }]
        action_id = uuid4()
        now = datetime.now(UTC)
        result = await self._run_executor(steps, {
            "dispatch_action": {
                "action_id": action_id, "success": True,
                "output": {}, "error": None,
                "started_at": now, "completed_at": now,
                "duration_seconds": 2.0, "logs": [],
            },
        })
        self.assertIsNone(result.error)
        self.assertEqual(len(result.execution.step_results), 1)
        self.assertTrue(result.execution.step_results[0].success)

    async def test_approval_pending_halts_execution(self) -> None:
        steps = [{
            "step_id": "s1", "action_type": "restart",
            "target_resource": "web-1",
            "target_resource_type": ResourceType.CONTAINER,
            "parameters": {}, "requires_approval": True,
            "description": "restart needs approval",
        }]
        result = await self._run_executor(steps, {
            "create_approval_request": "PENDING",
        })
        self.assertTrue(result.approval_pending)
        self.assertFalse(result.should_continue)
        self.assertEqual(len(result.execution.step_results), 0)

    async def test_approval_rejected_errors(self) -> None:
        steps = [{
            "step_id": "s1", "action_type": "restart",
            "target_resource": "web-1",
            "target_resource_type": ResourceType.CONTAINER,
            "parameters": {}, "requires_approval": True,
            "description": "restart needs approval",
        }]
        result = await self._run_executor(steps, {
            "create_approval_request": "REJECTED",
        })
        self.assertIn("rejected", (result.error or "").lower())

    async def test_step_failure_triggers_rollback(self) -> None:
        steps = [{
            "step_id": "s1", "action_type": "restart",
            "target_resource": "web-1",
            "target_resource_type": ResourceType.CONTAINER,
            "parameters": {}, "requires_approval": False,
            "description": "restart web",
            "rollback_action": {"action": "deploy", "version": "previous"},
        }]
        result = await self._run_executor(steps, {
            "dispatch_action": {
                "action_id": uuid4(), "success": False,
                "output": {}, "error": "Connection timeout",
                "started_at": datetime.now(UTC),
                "completed_at": datetime.now(UTC),
                "duration_seconds": 5.0, "logs": ["error: timeout"],
            },
            "initiate_rollback": {"success": True, "message": "Rolled back"},
        })
        self.assertTrue(result.execution.rollback_initiated)
        self.assertFalse(result.should_continue)

    async def test_step_failure_rollback_failure_errors(self) -> None:
        steps = [{
            "step_id": "s1", "action_type": "restart",
            "target_resource": "web-1",
            "target_resource_type": ResourceType.CONTAINER,
            "parameters": {}, "requires_approval": False,
            "description": "restart web",
            "rollback_action": {"action": "deploy"},
        }]
        result = await self._run_executor(steps, {
            "dispatch_action": {
                "action_id": uuid4(), "success": False,
                "output": {}, "error": "timeout",
                "started_at": datetime.now(UTC),
                "completed_at": datetime.now(UTC),
                "duration_seconds": 5.0, "logs": [],
            },
            "initiate_rollback": {"success": False, "error": "rollback also failed"},
        })
        self.assertIn("Rollback failed", result.error or "")

    async def test_two_steps_require_two_calls(self) -> None:
        """Each _process_task call processes exactly one step."""
        steps = [
            {
                "step_id": "s1", "action_type": "restart",
                "target_resource": "web-1",
                "target_resource_type": ResourceType.CONTAINER,
                "parameters": {}, "requires_approval": False,
                "description": "step 1",
            },
            {
                "step_id": "s2", "action_type": "verify",
                "target_resource": "web-1",
                "target_resource_type": ResourceType.CONTAINER,
                "parameters": {}, "requires_approval": False,
                "description": "step 2",
            },
        ]
        now = datetime.now(UTC)
        result = await self._run_executor(steps, {
            "dispatch_action": {
                "action_id": uuid4(), "success": True,
                "output": {}, "error": None,
                "started_at": now, "completed_at": now,
                "duration_seconds": 1.0, "logs": [],
            },
        })
        # After first call: step 0 processed, index advanced to 1
        self.assertEqual(result.execution.current_step_index, 1)
        self.assertEqual(len(result.execution.step_results), 1)
        self.assertTrue(result.execution.step_results[0].success)
        # Second call would process step 1


# ---------------------------------------------------------------------------
# Validator Agent
# ---------------------------------------------------------------------------


class ValidatorRunValidationTests(IsolatedAsyncioTestCase):
    """Validator._run_validation with mocked tools."""

    def setUp(self) -> None:
        self.agent = ValidatorAgent(config=AgentConfig(agent_type=AgentType.VALIDATOR))
        self.incident = _make_incident(services=["web"], resources=["res-1"])

    async def _run(self, tool_returns: dict[str, dict]) -> ValidatorState:
        state = ValidatorState()
        state.task = AgentTask(
            agent_type=AgentType.VALIDATOR,
            task_type="validate",
            input_data={},
        )
        state.incident = self.incident

        def _get(target: str, default: dict) -> dict:
            return tool_returns.get(target, default)

        with \
            patch("src.agents.validator.check_http_health", new=AsyncMock(return_value=_get("check_http_health", {"healthy": True, "message": "OK"}))), \
            patch("src.agents.validator.query_metrics_for_resource", new=AsyncMock(return_value=_get("query_metrics_for_resource", {"status": "healthy", "summary": "OK", "metrics": {}}))), \
            patch("src.agents.validator._run_synthetic_test", new=AsyncMock(return_value=_get("_run_synthetic_test", {"passed": True, "message": "OK", "duration_ms": 50, "test_type": "smoke", "target": ""}))), \
            patch("src.agents.validator._verify_alert_resolution", new=AsyncMock(return_value=_get("_verify_alert_resolution", {"all_resolved": True, "total_alerts": 0, "unresolved_count": 0, "unresolved_alerts": [], "summary": "All resolved"}))), \
            patch("src.agents.validator._check_incident_compliance", new=AsyncMock(return_value=_get("_check_incident_compliance", {"compliant": True, "summary": "OK", "rules_checked": 3, "rules_passed": 3, "violations": []}))), \
            patch("src.agents.validator._compare_resource_baselines", new=AsyncMock(return_value=_get("_compare_resource_baselines", {"all_within_baseline": True, "resources_checked": 1, "deviations": [], "summary": "OK"}))):
            await self.agent._process_task(state)

        return state

    async def test_all_checks_pass(self) -> None:
        state = await self._run({
            "check_http_health": {"healthy": True, "message": "OK"},
            "query_metrics_for_resource": {"status": "healthy", "summary": "OK", "metrics": {}},
            "_run_synthetic_test": {"passed": True, "message": "OK", "duration_ms": 50, "test_type": "smoke", "target": ""},
            "_verify_alert_resolution": {"all_resolved": True, "total_alerts": 0, "unresolved_count": 0, "unresolved_alerts": [], "summary": "All resolved"},
            "_check_incident_compliance": {"compliant": True, "summary": "OK", "rules_checked": 3, "rules_passed": 3, "violations": []},
            "_compare_resource_baselines": {"all_within_baseline": True, "resources_checked": 1, "deviations": [], "summary": "OK"},
        })
        self.assertEqual(state.validation_report.overall_status, "passed")
        self.assertGreater(state.validation_report.passed_checks, 0)
        self.assertEqual(state.validation_report.failed_checks, 0)

    async def test_health_check_failure_causes_failed_status(self) -> None:
        state = await self._run({
            "check_http_health": {"healthy": False, "message": "Unhealthy"},
            "query_metrics_for_resource": {"status": "healthy", "summary": "OK", "metrics": {}},
            "_run_synthetic_test": {"passed": True, "message": "OK", "duration_ms": 50, "test_type": "smoke", "target": ""},
            "_verify_alert_resolution": {"all_resolved": True, "total_alerts": 0, "unresolved_count": 0, "unresolved_alerts": [], "summary": "All resolved"},
            "_check_incident_compliance": {"compliant": True, "summary": "OK", "rules_checked": 3, "rules_passed": 3, "violations": []},
            "_compare_resource_baselines": {"all_within_baseline": True, "resources_checked": 1, "deviations": [], "summary": "OK"},
        })
        # health failure -> severity "critical" -> failed_checks > 0
        self.assertGreater(state.validation_report.failed_checks, 0)
        self.assertEqual(state.validation_report.overall_status, "failed")
        self.assertTrue(
            any("CRITICAL" in r for r in state.validation_report.recommendations)
        )


# ---------------------------------------------------------------------------
# Planner Agent
# ---------------------------------------------------------------------------


class PlannerBuildContextTests(IsolatedAsyncioTestCase):
    """Planner context building logic."""

    def setUp(self) -> None:
        self.agent = PlannerAgent(config=AgentConfig(agent_type=AgentType.PLANNER))

    def test_build_planning_context_includes_incident_details(self) -> None:
        state = PlannerState()
        state.incident = _make_incident(
            services=["web-api", "db"],
            resources=["web-1", "db-1"],
        )
        state.incident.root_cause = "CPU spike"
        ctx = self.agent._build_planning_context(state)
        self.assertIn("test incident", ctx)
        self.assertIn("SEV3", ctx)
        self.assertIn("APPLICATION", ctx)
        self.assertIn("CPU spike", ctx)
        self.assertIn("web-api, db", ctx)
        self.assertIn("web-1, db-1", ctx)

    def test_build_planning_context_without_incident(self) -> None:
        state = PlannerState()
        state.incident = _make_incident()
        state.incident.affected_services = []
        state.incident.affected_resources = []
        state.incident.root_cause = None
        ctx = self.agent._build_planning_context(state)
        self.assertIn("None", ctx)  # "None" for both services and resources
        self.assertIn("Unknown", ctx)  # root cause

    def test_build_planning_context_includes_kb_matches(self) -> None:
        state = PlannerState()
        state.incident = _make_incident()
        state.knowledge_matches = [
            {"title": "Runbook A", "content": "Restart the service"}
        ]
        ctx = self.agent._build_planning_context(state)
        self.assertIn("Runbook A", ctx)

    def test_build_planning_context_includes_similar_incidents(self) -> None:
        state = PlannerState()
        state.incident = _make_incident()
        state.similar_incidents = [
            {"title": "Past outage", "resolution": "Rebooted server"}
        ]
        ctx = self.agent._build_planning_context(state)
        self.assertIn("Past outage", ctx)
        self.assertIn("Rebooted server", ctx)
