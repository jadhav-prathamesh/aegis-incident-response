"""
Planner Agent - Creates remediation plans for incidents.
"""

from typing import Any
from uuid import UUID

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import BaseTool, tool
from pydantic import BaseModel, Field

from src.agents.base import BaseAgentState, ReactAgent
from src.core.config import get_settings
from src.core.knowledge_base import search_knowledge_entries
from src.core.logging import get_logger
from src.core.models import Incident, ResourceType
from src.core.similar_incidents import find_similar as _find_similar_incidents

logger = get_logger(__name__)
settings = get_settings()


class RemediationStep(BaseModel):
    """Single step in a remediation plan with action, target, dependencies, and rollback."""

    step_id: str
    action_type: str
    description: str
    target_resource: str
    target_resource_type: ResourceType
    parameters: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)
    estimated_duration_seconds: int = 60
    requires_approval: bool = False
    rollback_action: dict[str, Any] | None = None
    risk_level: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL


class RemediationPlan(BaseModel):
    """Complete remediation plan with ordered steps, risk assessment, and approval requirements."""

    plan_id: str
    incident_id: UUID
    title: str
    description: str
    steps: list[RemediationStep]
    total_estimated_duration_seconds: int
    risk_assessment: str
    requires_approval: bool
    created_by: str = "planner_agent"
    confidence_score: float = Field(ge=0.0, le=1.0)


class PlannerState(BaseAgentState):
    """State for the planner agent, holding incident context and knowledge search results."""

    incident: Incident | None = None
    plan: RemediationPlan | None = None
    knowledge_matches: list[dict[str, Any]] = Field(default_factory=list)
    similar_incidents: list[dict[str, Any]] = Field(default_factory=list)


class PlannerAgent(ReactAgent):
    """Agent that creates remediation plans for incidents."""

    def _get_specific_prompt(self) -> str:
        return (
            "You are the Planner Agent responsible for creating "
            "detailed remediation plans for IT incidents.\n\n"
            "Your responsibilities:\n"
            "1. Analyze the incident details, severity, affected services, "
            "and context\n"
            "2. Search knowledge base for relevant runbooks and similar "
            "incidents\n"
            "3. Create a step-by-step remediation plan with:\n"
            "   - Specific actions to take\n"
            "   - Target resources and parameters\n"
            "   - Dependencies between steps\n"
            "   - Risk assessment for each step\n"
            "   - Rollback procedures\n"
            "   - Approval requirements\n"
            "4. Estimate total execution time\n"
            "5. Determine if human approval is needed\n\n"
            "Available tools:\n"
            "- search_knowledge_base: Find relevant runbooks and procedures\n"
            "- find_similar_incidents: Find past incidents with similar "
            "patterns\n"
            "- get_resource_topology: Understand infrastructure dependencies\n"
            "- validate_plan: Check plan against policies and best practices\n\n"
            "Output format: Create a structured RemediationPlan "
            "with all steps."
        )

    def _get_tools(self) -> list[BaseTool]:
        return [
            search_knowledge_base,
            find_similar_incidents,
            get_resource_topology,
            validate_plan,
        ]

    def _get_state_class(self) -> type[BaseAgentState]:
        return PlannerState

    async def _process_task(self, state: PlannerState) -> PlannerState:
        """Process planning task."""
        task = state.task
        if not task:
            state.error = "No task provided"
            state.should_continue = False
            return state

        # Get incident from context
        incident_id = task.context.get("incident_id") or task.input_data.get("incident_id")
        if incident_id:
            state.incident = await self._get_incident(incident_id)

        if not state.incident:
            state.error = "No incident found for planning"
            state.should_continue = False
            return state

        # Search knowledge base
        kb_results = await search_knowledge_base.ainvoke({
            "query": f"{state.incident.category.value} {state.incident.severity.value} remediation",
            "category": "runbooks",
            "top_k": 5,
        })
        state.knowledge_matches = kb_results

        # Find similar incidents
        similar = await find_similar_incidents.ainvoke({
            "incident": state.incident.model_dump(),
            "limit": 5,
        })
        state.similar_incidents = similar

        # Create plan using LLM
        plan = await self._create_plan(state)
        state.plan = plan
        state.intermediate_results["plan"] = plan.model_dump()
        state.should_continue = False

        return state

    async def _create_plan(self, state: PlannerState) -> RemediationPlan:
        """Create remediation plan using an LLM with structured output."""
        context = self._build_planning_context(state)

        messages = [
            SystemMessage(content=self._get_system_prompt()),
            HumanMessage(content=context),
        ]

        # Get structured output
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model=self.config.model,
            temperature=0.1,
            max_tokens=4096,
        ).with_structured_output(RemediationPlan)

        plan = await llm.ainvoke(messages)
        return plan

    def _build_planning_context(self, state: PlannerState) -> str:
        """Build a formatted context string for the planner LLM call.

        Includes incident details, knowledge base matches, and similar past incidents.
        """
        incident = state.incident
        affected_services = (
            ', '.join(incident.affected_services) if incident.affected_services else 'None'
        )
        affected_resources = (
            ', '.join(incident.affected_resources) if incident.affected_resources else 'None'
        )
        parts = [
            "INCIDENT TO PLAN FOR:",
            f"  ID: {incident.id}",
            f"  Title: {incident.title}",
            f"  Severity: {incident.severity}",
            f"  Category: {incident.category}",
            f"  Description: {incident.description}",
            f"  Affected Services: {affected_services}",
            f"  Affected Resources: {affected_resources}",
            f"  Root Cause: {incident.root_cause or 'Unknown'}",
            "",
        ]

        if state.knowledge_matches:
            parts.append("RELEVANT KNOWLEDGE BASE ENTRIES:")
            for match in state.knowledge_matches[:3]:
                title = match.get('title', 'Unknown')
                content = match.get('content', '')[:200]
                parts.append(f"  - {title}: {content}")
            parts.append("")

        if state.similar_incidents:
            parts.append("SIMILAR PAST INCIDENTS:")
            for sim in state.similar_incidents[:3]:
                title = sim.get('title', 'Unknown')
                resolution = sim.get('resolution', 'No resolution')[:200]
                parts.append(f"  - {title}: {resolution}")
            parts.append("")

        parts.append(
            "Create a detailed remediation plan with specific steps, "
            "dependencies, risks, and rollback procedures."
        )
        return "\n".join(parts)


# Tools for Planner Agent
@tool
async def search_knowledge_base(
    query: str,
    category: str = "runbooks",
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Search knowledge base for relevant entries."""
    logger.info("Searching knowledge base", query=query, category=category)
    return await search_knowledge_entries(query=query, category=category, top_k=top_k)


@tool
async def find_similar_incidents(
    incident: dict[str, Any],
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Find similar past incidents."""
    logger.info("Finding similar incidents", incident_id=incident.get("id"))
    try:
        inc = Incident(**incident)
        return await _find_similar_incidents(inc, limit=limit)
    except Exception as exc:
        logger.warning("Similar incident search failed", error=str(exc))
        return []


@tool
async def get_resource_topology(
    resource_id: str,
    depth: int = 2,
) -> dict[str, Any]:
    """Get infrastructure topology around a resource.

    This is a stub implementation that returns an empty topology.
    Replace with actual infrastructure discovery (e.g., Kubernetes
    dependencies, service mesh, or CMDB queries).
    """
    logger.info("Getting resource topology", resource_id=resource_id)
    return {
        "resource_id": resource_id,
        "dependencies": [],
        "dependents": [],
    }


@tool
async def validate_plan(
    plan: dict[str, Any],
) -> dict[str, Any]:
    """Validate plan against policies and best practices.

    This is a stub implementation that always returns valid.
    Replace with actual policy engine (e.g., OPA, custom rules).
    """
    logger.info("Validating plan", plan_id=plan.get("plan_id"))
    return {"valid": True, "warnings": [], "errors": []}


# Export
__all__ = ["PlannerAgent", "PlannerState", "RemediationPlan", "RemediationStep"]
