"""Behavioural tests for Orchestrator Agent decision-making and workflow control."""

from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.agents.orchestrator import OrchestratorAgent, OrchestratorState
from src.core.models import (
    AgentConfig,
    AgentTask,
    AgentType,
    Incident,
    IncidentCategory,
    IncidentSeverity,
    IncidentStatus,
)


def _make_incident(
    severity: IncidentSeverity = IncidentSeverity.SEV3,
    status: IncidentStatus = IncidentStatus.OPEN,
) -> Incident:
    return Incident(
        id=uuid4(),
        title="test",
        description="test incident",
        severity=severity,
        status=status,
        category=IncidentCategory.APPLICATION,
        source="test",
    )


def _llm_response(content: str) -> MagicMock:
    m = MagicMock()
    m.content = content
    return m


class FallbackDecisionTests(IsolatedAsyncioTestCase):
    """Deterministic fallback decision tree — no LLM needed."""

    def setUp(self) -> None:
        self.agent = OrchestratorAgent(config=AgentConfig(agent_type=AgentType.ORCHESTRATOR))

    def test_no_incident_plans(self) -> None:
        state = OrchestratorState()
        state.incident = None
        d = self.agent._fallback_decision(state)
        self.assertEqual(d.action, "plan")
        self.assertEqual(d.next_agent, AgentType.PLANNER)
        self.assertAlmostEqual(d.confidence, 0.7)

    def test_open_sev1_plans_high_confidence(self) -> None:
        state = OrchestratorState()
        state.incident = _make_incident(IncidentSeverity.SEV1, IncidentStatus.OPEN)
        d = self.agent._fallback_decision(state)
        self.assertEqual(d.action, "plan")
        self.assertAlmostEqual(d.confidence, 0.9)

    def test_open_sev2_plans_high_confidence(self) -> None:
        state = OrchestratorState()
        state.incident = _make_incident(IncidentSeverity.SEV2, IncidentStatus.OPEN)
        d = self.agent._fallback_decision(state)
        self.assertEqual(d.action, "plan")
        self.assertAlmostEqual(d.confidence, 0.9)

    def test_open_lower_severity_plans_medium_confidence(self) -> None:
        for sev in (IncidentSeverity.SEV3, IncidentSeverity.SEV4, IncidentSeverity.SEV5):
            with self.subTest(sev=sev):
                state = OrchestratorState()
                state.incident = _make_incident(sev, IncidentStatus.OPEN)
                d = self.agent._fallback_decision(state)
                self.assertEqual(d.action, "plan")
                self.assertAlmostEqual(d.confidence, 0.8)

    def test_investigating_without_planner_plans(self) -> None:
        state = OrchestratorState()
        state.incident = _make_incident(IncidentSeverity.SEV1, IncidentStatus.INVESTIGATING)
        state.completed_agents = []
        d = self.agent._fallback_decision(state)
        self.assertEqual(d.action, "plan")
        self.assertEqual(d.next_agent, AgentType.PLANNER)

    def test_investigating_planner_done_executes(self) -> None:
        state = OrchestratorState()
        state.incident = _make_incident(IncidentSeverity.SEV1, IncidentStatus.INVESTIGATING)
        state.completed_agents = [AgentType.PLANNER]
        d = self.agent._fallback_decision(state)
        self.assertEqual(d.action, "execute")
        self.assertEqual(d.next_agent, AgentType.EXECUTOR)

    def test_resolving_without_validator_validates(self) -> None:
        state = OrchestratorState()
        state.incident = _make_incident(IncidentSeverity.SEV1, IncidentStatus.RESOLVING)
        state.completed_agents = [AgentType.PLANNER, AgentType.EXECUTOR]
        d = self.agent._fallback_decision(state)
        self.assertEqual(d.action, "validate")
        self.assertEqual(d.next_agent, AgentType.VALIDATOR)

    def test_resolved_with_validator_closes(self) -> None:
        state = OrchestratorState()
        state.incident = _make_incident(IncidentSeverity.SEV3, IncidentStatus.RESOLVED)
        state.completed_agents = [AgentType.PLANNER, AgentType.EXECUTOR, AgentType.VALIDATOR]
        d = self.agent._fallback_decision(state)
        self.assertEqual(d.action, "close")
        self.assertIsNone(d.next_agent)

    def test_unknown_status_observes(self) -> None:
        state = OrchestratorState()
        state.incident = _make_incident(IncidentSeverity.SEV3, IncidentStatus.ACKNOWLEDGED)
        d = self.agent._fallback_decision(state)
        self.assertEqual(d.action, "observe")
        self.assertEqual(d.next_agent, AgentType.OBSERVER)


class ShouldContinueTests(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.agent = OrchestratorAgent(config=AgentConfig(agent_type=AgentType.ORCHESTRATOR))

    def test_error_ends(self) -> None:
        state = OrchestratorState()
        state.error = "something broke"
        self.assertEqual(self.agent._should_continue(state), "end")

    def test_should_continue_false_ends(self) -> None:
        state = OrchestratorState()
        state.should_continue = False
        self.assertEqual(self.agent._should_continue(state), "end")

    def test_no_decisions_continues(self) -> None:
        state = OrchestratorState()
        self.assertEqual(self.agent._should_continue(state), "continue")

    def test_plan_without_tools_continues(self) -> None:
        state = OrchestratorState()
        state.decisions.append(
            MagicMock(next_agent=AgentType.PLANNER, action="plan", payload={})
        )
        self.assertEqual(self.agent._should_continue(state), "continue")

    def test_execute_with_agent_continues(self) -> None:
        state = OrchestratorState()
        state.decisions.append(
            MagicMock(next_agent=AgentType.EXECUTOR, action="execute", payload={})
        )
        self.assertEqual(self.agent._should_continue(state), "continue")

    def test_close_no_next_agent_continues(self) -> None:
        state = OrchestratorState()
        state.decisions.append(MagicMock(next_agent=None, action="close", payload={}))
        self.assertEqual(self.agent._should_continue(state), "continue")


class ExecuteDecisionTests(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.agent = OrchestratorAgent(config=AgentConfig(agent_type=AgentType.ORCHESTRATOR))

    async def test_plan_decision_stores_planner_task(self) -> None:
        state = OrchestratorState()
        state.incident = _make_incident()
        state.workflow_id = uuid4()
        from src.agents.orchestrator import OrchestratorDecision

        decision = OrchestratorDecision(
            action="plan",
            reason="need plan",
            next_agent=AgentType.PLANNER,
            confidence=0.9,
        )
        result = await self.agent._execute_decision(state, decision)
        key = "PLANNER_task"
        self.assertIn(key, result.intermediate_results)
        task = result.intermediate_results[key]
        self.assertEqual(task["agent_type"], AgentType.PLANNER)
        self.assertEqual(task["task_type"], "plan")

    async def test_execute_decision_stores_executor_task(self) -> None:
        state = OrchestratorState()
        state.incident = _make_incident()
        state.workflow_id = uuid4()
        from src.agents.orchestrator import OrchestratorDecision

        decision = OrchestratorDecision(
            action="execute",
            reason="plan ready",
            next_agent=AgentType.EXECUTOR,
            confidence=0.9,
        )
        result = await self.agent._execute_decision(state, decision)
        self.assertIn("EXECUTOR_task", result.intermediate_results)

    async def test_close_updates_incident_status(self) -> None:
        state = OrchestratorState()
        state.incident = _make_incident(status=IncidentStatus.RESOLVED)
        from src.agents.orchestrator import OrchestratorDecision

        decision = OrchestratorDecision(
            action="close", reason="resolved", confidence=0.95
        )
        result = await self.agent._execute_decision(state, decision)
        self.assertEqual(result.incident.status, IncidentStatus.CLOSED)
        self.assertIsNotNone(result.incident.closed_at)

    async def test_escalate_acknowledges_incident(self) -> None:
        state = OrchestratorState()
        state.incident = _make_incident()
        from src.agents.orchestrator import OrchestratorDecision

        decision = OrchestratorDecision(
            action="escalate",
            reason="auto escalate",
            payload={"reason": "test"},
            confidence=0.5,
        )
        result = await self.agent._execute_decision(state, decision)
        self.assertEqual(result.incident.status, IncidentStatus.ACKNOWLEDGED)


class ProcessTaskTests(IsolatedAsyncioTestCase):
    """End-to-end _process_task with mocked LLM."""

    def setUp(self) -> None:
        self.agent = OrchestratorAgent(config=AgentConfig(agent_type=AgentType.ORCHESTRATOR))

    async def test_no_task_sets_error(self) -> None:
        state = OrchestratorState()
        result = await self.agent._process_task(state)
        self.assertIsNotNone(result.error)

    async def test_plan_flow_with_mocked_llm(self) -> None:
        state = OrchestratorState()
        state.task = AgentTask(
            agent_type=AgentType.ORCHESTRATOR,
            task_type="orchestrate",
            input_data={},
        )
        state.incident = _make_incident(IncidentSeverity.SEV3, IncidentStatus.OPEN)
        self.agent._call_llm = AsyncMock(
            return_value=_llm_response(
                '{"action": "plan", "reason": "Need plan", '
                '"next_agent": "PLANNER", "payload": {}, "confidence": 0.85}'
            )
        )
        result = await self.agent._process_task(state)
        self.assertIsNone(result.error)
        self.assertEqual(len(result.decisions), 1)
        self.assertEqual(result.decisions[0].action, "plan")
        self.assertIn("PLANNER_task", result.intermediate_results)
        self.assertTrue(result.should_continue)

    async def test_close_flow_sets_should_continue_false(self) -> None:
        state = OrchestratorState()
        state.task = AgentTask(
            agent_type=AgentType.ORCHESTRATOR,
            task_type="orchestrate",
            input_data={},
        )
        state.incident = _make_incident(IncidentSeverity.SEV3, IncidentStatus.RESOLVED)
        self.agent._call_llm = AsyncMock(
            return_value=_llm_response(
                '{"action": "close", "reason": "All resolved", '
                '"next_agent": null, "payload": {}, "confidence": 0.95}'
            )
        )
        result = await self.agent._process_task(state)
        self.assertFalse(result.should_continue)
        self.assertEqual(result.incident.status, IncidentStatus.CLOSED)

    async def test_llm_error_propagates(self) -> None:
        """LLM exceptions propagate up (try/except only covers JSON parsing)."""
        state = OrchestratorState()
        state.task = AgentTask(
            agent_type=AgentType.ORCHESTRATOR,
            task_type="orchestrate",
            input_data={},
        )
        state.incident = _make_incident(IncidentSeverity.SEV1, IncidentStatus.OPEN)
        self.agent._call_llm = AsyncMock(side_effect=ValueError("LLM down"))
        with self.assertRaises(ValueError):
            await self.agent._process_task(state)

    async def test_llm_invalid_json_falls_back(self) -> None:
        state = OrchestratorState()
        state.task = AgentTask(
            agent_type=AgentType.ORCHESTRATOR,
            task_type="orchestrate",
            input_data={},
        )
        state.incident = _make_incident(IncidentSeverity.SEV3, IncidentStatus.OPEN)
        self.agent._call_llm = AsyncMock(
            return_value=_llm_response("not json at all")
        )
        result = await self.agent._process_task(state)
        self.assertEqual(result.decisions[0].action, "plan")
        self.assertAlmostEqual(result.decisions[0].confidence, 0.8)

    async def test_task_with_incident_id_loads_incident(self) -> None:
        state = OrchestratorState()
        state.task = AgentTask(
            agent_type=AgentType.ORCHESTRATOR,
            task_type="orchestrate",
            input_data={"incident_id": uuid4()},
        )
        self.agent._get_incident = AsyncMock(
            return_value=_make_incident(IncidentSeverity.SEV2, IncidentStatus.OPEN)
        )
        self.agent._call_llm = AsyncMock(
            return_value=_llm_response(
                '{"action": "plan", "reason": "loaded", '
                '"next_agent": "PLANNER", "payload": {}, "confidence": 0.9}'
            )
        )
        result = await self.agent._process_task(state)
        self.assertIsNotNone(result.incident)
        self.assertEqual(result.incident.severity, IncidentSeverity.SEV2)
