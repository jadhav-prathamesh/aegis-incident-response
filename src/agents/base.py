"""Base agent classes and common functionality for agents."""

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field

from src.core.config import get_settings
from src.core.logging import get_logger
from src.core.models import AgentConfig, AgentResult, AgentTask, AgentType, Incident

logger = get_logger(__name__)
settings = get_settings()


class BaseAgentState(BaseModel):
    """Base state for all agents in the LangGraph workflow.

    Tracks task context, message history, intermediate results, iteration count,
    and completion signals shared by every agent implementation.
    """

    task: AgentTask | None = None
    incident_id: UUID | None = None
    workflow_id: UUID | None = None
    messages: list[BaseMessage] = Field(default_factory=list)
    intermediate_results: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    should_continue: bool = True
    iterations: int = 0
    max_iterations: int = 10
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    def __init__(self, config: AgentConfig | None = None):
        config = config or self._default_config()
        self.config = config
        self.agent_type = AgentType(config.agent_type)
        self.llm: BaseChatModel | None = None
        self.tools: list[BaseTool] = []
        self.graph: StateGraph | None = None
        self._initialized = False

    @abstractmethod
    def _get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        pass

    def _default_config(self) -> AgentConfig:
        """Build a default agent configuration."""
        return AgentConfig(
            agent_type=self.agent_type,
            model=settings.llm.model,
            temperature=settings.agent.default_temperature,
            max_tokens=settings.agent.default_max_tokens,
            timeout_seconds=settings.agent.default_timeout,
            max_retries=settings.agent.max_retries,
        )

    @abstractmethod
    def _get_tools(self) -> list[BaseTool]:
        """Get the tools available to this agent."""
        pass

    @abstractmethod
    def _get_state_class(self) -> type[BaseAgentState]:
        """Get the state class for this agent's graph."""
        pass

    @abstractmethod
    async def _process_task(self, state: BaseAgentState) -> BaseAgentState:
        """Process the task - main logic for the agent."""
        pass

    def _should_continue(self, state: BaseAgentState) -> str:
        """Determine if the agent should continue or end.

        Returns "end" when an error occurred, the agent signals completion,
        or the iteration limit has been reached. Returns "continue" otherwise.
        """
        if state.error:
            return "end"
        if not state.should_continue:
            return "end"
        if state.iterations >= state.max_iterations:
            state.error = f"Max iterations ({state.max_iterations}) reached"
            return "end"
        return "continue"

    async def initialize(self) -> None:
        """Initialize the agent with LLM and tools."""
        if self._initialized:
            return

        logger.info("Initializing agent", agent_type=self.agent_type.value)

        # Initialize LLM
        self.llm = await self._create_llm()

        # Get tools
        self.tools = self._get_tools()

        # Bind tools to LLM
        if self.tools:
            self.llm = self.llm.bind_tools(self.tools)

        # Build graph
        self.graph = await self._build_graph()

        self._initialized = True
        logger.info("Agent initialized", agent_type=self.agent_type.value)

    async def _create_llm(self) -> BaseChatModel:
        """Create LLM instance based on agent configuration."""
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            timeout=self.config.timeout_seconds,
            max_retries=self.config.max_retries,
            api_key=settings.llm.api_key,
            base_url=settings.llm.base_url,
        )

    async def _build_graph(self) -> StateGraph:
        """Build the LangGraph state graph with process and tool nodes."""
        state_class = self._get_state_class()

        # Define the graph
        workflow = StateGraph(state_class)

        # Add nodes
        workflow.add_node("process", self._run_process_task)
        workflow.add_node("tools", ToolNode(self.tools))

        # Add edges
        workflow.set_entry_point("process")
        workflow.add_conditional_edges(
            "process",
            self._should_continue,
            {
                "continue": "tools",
                "end": END,
            },
        )
        workflow.add_edge("tools", "process")

        # Compile with checkpointer
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)

    async def _run_process_task(self, state: BaseAgentState) -> BaseAgentState:
        """Wrapper for processing task."""
        state.iterations += 1
        return await self._process_task(state)

    async def _call_llm(self, messages: list[BaseMessage]) -> BaseMessage:
        """Call the configured LLM."""
        if self.llm is None:
            self.llm = await self._create_llm()
        return await self.llm.ainvoke(messages)

    async def execute(self, task: AgentTask) -> AgentResult:
        """Execute the agent with a given task."""
        if not self._initialized:
            await self.initialize()

        start_time = datetime.now(UTC)
        logger.info(
            "Executing agent task",
            agent_type=self.agent_type.value,
            task_id=str(task.task_id),
        )

        try:
            # Prepare initial state
            state = self._get_state_class()(
                task=task,
                workflow_id=task.context.get("workflow_id"),
                incident_id=task.context.get("incident_id"),
            )

            # Run the graph
            config = {"configurable": {"thread_id": str(task.task_id)}}
            final_state = await self.graph.ainvoke(state, config)

            # Extract result
            execution_time = (datetime.now(UTC) - start_time).total_seconds() * 1000

            result = AgentResult(
                task_id=task.task_id,
                agent_type=self.agent_type,
                success=final_state.error is None,
                output=final_state.intermediate_results,
                error=final_state.error,
                execution_time_ms=int(execution_time),
                confidence_score=self._calculate_confidence(final_state),
            )

            logger.info(
                "Agent execution completed",
                agent_type=self.agent_type.value,
                task_id=str(task.task_id),
                success=result.success,
                execution_time_ms=result.execution_time_ms,
            )

            return result

        except Exception as e:
            execution_time = (datetime.now(UTC) - start_time).total_seconds() * 1000
            logger.error("Agent execution failed", agent_type=self.agent_type.value, error=str(e))

            return AgentResult(
                task_id=task.task_id,
                agent_type=self.agent_type,
                success=False,
                error=str(e),
                execution_time_ms=int(execution_time),
            )

    def _calculate_confidence(self, state: BaseAgentState) -> float:
        """Calculate confidence score based on state."""
        # Default implementation - can be overridden
        if state.error:
            return 0.0
        if state.intermediate_results.get("validated", False):
            return 0.95
        if state.iterations == 1:
            return 0.8
        return max(0.5, 0.9 - (state.iterations * 0.1))

    async def health_check(self) -> dict[str, Any]:
        """Check agent health."""
        return {
            "agent_type": self.agent_type.value,
            "initialized": self._initialized,
            "llm_configured": self.llm is not None,
            "tools_count": len(self.tools),
            "config": {
                "model": self.config.model,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
            },
        }


class ReactAgent(BaseAgent):
    """ReAct (Reasoning + Acting) pattern agent."""

    def _get_system_prompt(self) -> str:
        agent_type = self.agent_type.value
        specific = self._get_specific_prompt()
        return (
            f"You are a {agent_type} agent in the "
            "Aegis.\n\n"
            f"{specific}\n\n"
            "Follow the ReAct pattern:\n"
            "1. THOUGHT: Analyze the situation and reason about what to do\n"
            "2. ACTION: Use available tools to gather information or take action\n"
            "3. OBSERVATION: Review the results of your actions\n"
            "4. Repeat until you have enough information to complete the task\n\n"
            "Always provide your reasoning before taking actions. "
            "Be thorough but efficient."
        )

    @abstractmethod
    def _get_specific_prompt(self) -> str:
        """Get agent-specific prompt addition."""
        pass

    async def _process_task(self, state: BaseAgentState) -> BaseAgentState:
        """Process task using ReAct pattern."""
        task = state.task
        if not task:
            state.error = "No task provided"
            state.should_continue = False
            return state

        # Build messages
        messages = [
            SystemMessage(content=self._get_system_prompt()),
        ]

        # Add context
        context = self._build_context(state)
        if context:
            messages.append(HumanMessage(content=context))

        # Add task
        messages.append(HumanMessage(content=f"Task: {task.task_type}\nInput: {task.input_data}"))

        # Invoke LLM
        response = await self.llm.ainvoke(messages)
        state.messages.append(response)

        # Check for tool calls
        if response.tool_calls:
            # Tools will be executed by the graph
            state.intermediate_results["tool_calls"] = [
                {"name": tc["name"], "args": tc["args"]} for tc in response.tool_calls
            ]
            state.should_continue = True
        else:
            # No tool calls, task complete
            state.intermediate_results["final_response"] = response.content
            state.should_continue = False

        return state

    def _build_context(self, state: BaseAgentState) -> str:
        """Build context message for the agent."""
        parts = []

        if state.incident_id:
            parts.append(f"Incident ID: {state.incident_id}")
        if state.workflow_id:
            parts.append(f"Workflow ID: {state.workflow_id}")

        if state.intermediate_results:
            parts.append("Previous Results:")
            for key, value in state.intermediate_results.items():
                parts.append(f"  {key}: {value}")

        if state.messages:
            parts.append(f"Message History: {len(state.messages)} messages")

        return "\n".join(parts) if parts else ""

    async def _get_incident(self, incident_id: UUID) -> Incident | None:
        from src.core.incident_store import get_incident
        return get_incident(incident_id)


# Agent factory
_agent_instances: dict[AgentType, BaseAgent] = {}


def get_agent(agent_type: AgentType) -> BaseAgent:
    """Get or create agent instance."""
    if agent_type not in _agent_instances:
        from src.agents.executor import ExecutorAgent
        from src.agents.observer import ObserverAgent
        from src.agents.orchestrator import OrchestratorAgent
        from src.agents.planner import PlannerAgent
        from src.agents.validator import ValidatorAgent

        agent_classes = {
            AgentType.ORCHESTRATOR: OrchestratorAgent,
            AgentType.PLANNER: PlannerAgent,
            AgentType.EXECUTOR: ExecutorAgent,
            AgentType.OBSERVER: ObserverAgent,
            AgentType.VALIDATOR: ValidatorAgent,
        }

        if agent_type in agent_classes:
            config = AgentConfig(agent_type=agent_type)
            _agent_instances[agent_type] = agent_classes[agent_type](config)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

    return _agent_instances[agent_type]
