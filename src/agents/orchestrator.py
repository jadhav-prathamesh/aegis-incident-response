"""
Orchestrator Agent - Coordinates multi-agent workflows for incident management.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.agents.base import BaseAgent, BaseAgentState
from src.core.config import get_settings
from src.core.incident_store import save_incident
from src.core.logging import get_logger
from src.core.models import (
    AgentConfig,
    AgentTask,
    AgentType,
    Incident,
    IncidentSeverity,
    IncidentStatus,
)
from src.core.similar_incidents import index_incident

logger = get_logger(__name__)
settings = get_settings()


class OrchestratorDecision(BaseModel):
    """Decision made by the orchestrator after analyzing an incident.

    Attributes:
        action: One of "plan", "execute", "observe", "validate", "escalate", "close".
        reason: Human-readable explanation of the decision.
        next_agent: Agent type to delegate the next step to.
        payload: Additional data to pass to the next agent.
        confidence: How certain the orchestrator is about this decision (0.0-1.0).
    """

    action: str  # "plan", "execute", "observe", "validate", "escalate", "close"
    reason: str
    next_agent: AgentType | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)


class OrchestratorState(BaseAgentState):
    """Extended state for the orchestrator agent.

    Tracks the current incident, workflow decisions, completed agents,
    and pending human approvals.
    """

    incident: Incident | None = None
    workflow_id: UUID | None = None
    decisions: list[OrchestratorDecision] = Field(default_factory=list)
    completed_agents: list[AgentType] = Field(default_factory=list)
    pending_approvals: list[dict[str, Any]] = Field(default_factory=list)


class OrchestratorAgent(BaseAgent):
    """Main orchestrator that coordinates all other agents."""

    def _default_config(self) -> AgentConfig:
        return AgentConfig(
            agent_type=AgentType.ORCHESTRATOR,
            model=settings.llm.model,
            temperature=0.1,
            max_tokens=4096,
            timeout_seconds=300,
            max_retries=3,
            system_prompt=self._get_system_prompt(),
            tools=[
                "create_incident",
                "update_incident",
                "get_incident",
                "list_incidents",
                "trigger_planner",
                "trigger_executor",
                "trigger_observer",
                "trigger_validator",
                "request_approval",
                "send_notification",
                "escalate_incident",
            ],
        )

    def _get_system_prompt(self) -> str:
        return """You are the Orchestrator Agent for Aegis.

Your role is to coordinate multi-agent workflows for intelligent incident
management, root cause analysis, and self-healing infrastructure.

RESPONSIBILITIES:
1. Receive incidents from monitoring systems or manual creation
2. Analyze incident severity, category, and context
3. Decide on the appropriate workflow: planning, execution, observation, validation
4. Coordinate between Planner, Executor, Observer, and Validator agents
5. Handle human-in-the-loop approvals for critical actions
6. Manage incident lifecycle from detection to resolution
7. Escalate when automated resolution fails or requires human intervention

DECISION FRAMEWORK:
- SEV1/SEV2 incidents: Immediate planning + execution with parallel observation
- SEV3 incidents: Standard planning -> execution -> validation workflow
- SEV4/SEV5 incidents: Automated resolution with observer monitoring
- Known patterns: Use runbook-based execution
- Unknown patterns: Full planning + RCA analysis

COMMUNICATION:
- Send tasks to agents via message bus
- Collect results and make decisions
- Request human approval for destructive actions
- Notify stakeholders at key milestones

OUTPUT FORMAT:
Always respond with a structured decision:
{
  "action": "plan|execute|observe|validate|escalate|close",
  "reason": "Detailed reasoning",
  "next_agent": "PLANNER|EXECUTOR|OBSERVER|VALIDATOR|null",
  "payload": {...},
  "confidence": 0.0-1.0
}"""

    def _get_tools(self) -> list[BaseTool]:
        """Return orchestrator tools. Currently no direct tools are bound."""
        return []

    def _get_state_class(self) -> type[BaseAgentState]:
        return OrchestratorState

    async def _process_task(self, state: OrchestratorState) -> OrchestratorState:
        """Process orchestration task."""
        task = state.task
        if not task:
            state.error = "No task provided"
            state.should_continue = False
            return state

        # Initialize incident if provided
        if "incident_id" in task.input_data:
            incident = await self._get_incident(task.input_data["incident_id"])
            if incident:
                state.incident = incident

        # If new incident, create it
        if "create_incident" in task.input_data:
            incident = await self._create_incident(task.input_data["create_incident"])
            state.incident = incident

        # Analyze and decide next action
        decision = await self._make_decision(state)
        state.decisions.append(decision)

        # Execute decision
        state = await self._execute_decision(state, decision)

        # Check if workflow complete
        if decision.action in ["close", "escalate"]:
            state.should_continue = False

        return state

    def _should_continue(self, state: OrchestratorState) -> str:
        """Determine next step."""
        if state.error:
            return "end"

        if not state.should_continue:
            return "end"

        # Check last decision
        if state.decisions:
            last_decision = state.decisions[-1]
            if last_decision.next_agent:
                if last_decision.action == "plan":
                    return "tools" if last_decision.payload.get("use_tools") else "continue"
                return "continue"

        return "continue"

    async def _make_decision(self, state: OrchestratorState) -> OrchestratorDecision:
        """Make orchestration decision using LLM."""
        # Build context for decision
        context = self._build_decision_context(state)

        messages = [
            SystemMessage(content=self._get_system_prompt()),
            HumanMessage(content=context),
        ]

        response = await self._call_llm(messages)

        # Parse decision from response
        try:
            import json
            decision_data = json.loads(response.content)
            return OrchestratorDecision(**decision_data)
        except Exception as e:
            logger.warning("Failed to parse orchestrator decision, using fallback", error=str(e))
            return self._fallback_decision(state)

    def _build_decision_context(self, state: OrchestratorState) -> str:
        """Build context for decision making."""
        parts = []

        if state.incident:
            parts.append(f"INCIDENT: {state.incident.title}")
            parts.append(f"Severity: {state.incident.severity}")
            parts.append(f"Status: {state.incident.status}")
            parts.append(f"Category: {state.incident.category}")
            parts.append(f"Description: {state.incident.description}")
            if state.incident.affected_services:
                parts.append(f"Affected Services: {', '.join(state.incident.affected_services)}")
            if state.incident.root_cause:
                parts.append(f"Root Cause: {state.incident.root_cause}")

        parts.append(f"\nWorkflow ID: {state.workflow_id}")
        parts.append(f"Completed Agents: {[a.value for a in state.completed_agents]}")
        parts.append(f"Pending Approvals: {len(state.pending_approvals)}")

        if state.decisions:
            parts.append("\nPrevious Decisions:")
            for d in state.decisions[-3:]:
                parts.append(f"  - {d.action}: {d.reason} (confidence: {d.confidence})")

        parts.append("\nWhat should be the next action? Respond with JSON decision format.")

        return "\n".join(parts)

    def _fallback_decision(self, state: OrchestratorState) -> OrchestratorDecision:
        """Fallback decision logic when LLM fails."""
        if not state.incident:
            return OrchestratorDecision(
                action="plan",
                reason="No incident context, starting planning phase",
                next_agent=AgentType.PLANNER,
                confidence=0.7,
            )

        # Check incident status
        if state.incident.status == IncidentStatus.OPEN:
            if state.incident.severity in [IncidentSeverity.SEV1, IncidentSeverity.SEV2]:
                return OrchestratorDecision(
                    action="plan",
                    reason=(
                        f"High severity incident ({state.incident.severity}) "
                        "requires immediate planning"
                    ),
                    next_agent=AgentType.PLANNER,
                    confidence=0.9,
                )
            return OrchestratorDecision(
                action="plan",
                reason="New incident requires planning",
                next_agent=AgentType.PLANNER,
                confidence=0.8,
            )

        if state.incident.status == IncidentStatus.INVESTIGATING:
            if AgentType.PLANNER not in state.completed_agents:
                return OrchestratorDecision(
                    action="plan",
                    reason="Incident under investigation, need planning",
                    next_agent=AgentType.PLANNER,
                    confidence=0.8,
                )
            if AgentType.EXECUTOR not in state.completed_agents:
                return OrchestratorDecision(
                    action="execute",
                    reason="Plan ready, executing remediation",
                    next_agent=AgentType.EXECUTOR,
                    confidence=0.8,
                )

        if state.incident.status in [IncidentStatus.RESOLVING, IncidentStatus.RESOLVED]:
            if AgentType.VALIDATOR not in state.completed_agents:
                return OrchestratorDecision(
                    action="validate",
                    reason="Resolution implemented, validating fix",
                    next_agent=AgentType.VALIDATOR,
                    confidence=0.8,
                )
            return OrchestratorDecision(
                action="close",
                reason="Incident resolved and validated",
                confidence=0.9,
            )

        return OrchestratorDecision(
            action="observe",
            reason="Monitoring incident progress",
            next_agent=AgentType.OBSERVER,
            confidence=0.7,
        )

    async def _execute_decision(
        self,
        state: OrchestratorState,
        decision: OrchestratorDecision,
    ) -> OrchestratorState:
        """Execute the orchestrator's decision."""
        if decision.next_agent:
            # Create task for next agent
            agent_task = AgentTask(
                agent_type=decision.next_agent,
                task_type=decision.action,
                input_data=decision.payload,
                context={
                    "incident_id": str(state.incident.id) if state.incident else None,
                    "workflow_id": str(state.workflow_id) if state.workflow_id else None,
                    "orchestrator_decision": decision.model_dump(),
                },
            )

            # Send to agent via message bus (simplified)
            key = f"{decision.next_agent.value}_task"
            state.intermediate_results[key] = agent_task.model_dump()

            if decision.next_agent == AgentType.PLANNER:
                state.completed_agents.append(AgentType.PLANNER)
            elif decision.next_agent == AgentType.EXECUTOR:
                state.completed_agents.append(AgentType.EXECUTOR)
            elif decision.next_agent == AgentType.OBSERVER:
                state.completed_agents.append(AgentType.OBSERVER)
            elif decision.next_agent == AgentType.VALIDATOR:
                state.completed_agents.append(AgentType.VALIDATOR)

        # Handle specific actions
        if decision.action == "escalate":
            reason = decision.payload.get("reason", "Auto-escalation")
            await self._escalate_incident(state.incident, reason)
            if state.incident:
                state.incident.status = IncidentStatus.ACKNOWLEDGED

        elif decision.action == "close":
            if state.incident:
                state.incident.status = IncidentStatus.CLOSED
                state.incident.closed_at = datetime.now(UTC)
                await self._update_incident(state.incident)

        return state

    async def _create_incident(self, incident_data: dict) -> Incident:
        """Create a new incident, persist it, and index for similarity search."""
        incident = Incident(**incident_data)
        saved = save_incident(incident)
        await index_incident(saved)
        return saved

    async def _update_incident(self, incident: Incident) -> Incident:
        """Persist updated incident to the store."""
        return save_incident(incident)

    async def _escalate_incident(self, incident: Incident | None, reason: str) -> None:
        """Log an escalation event so a human operator can intervene."""
        inc_id = str(incident.id) if incident else None
        logger.warning("Escalating incident", incident_id=inc_id, reason=reason)
