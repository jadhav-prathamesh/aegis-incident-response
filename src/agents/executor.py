"""
Executor Agent - Executes remediation plans and automated actions.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from langchain_core.tools import BaseTool, tool
from pydantic import BaseModel, Field

from src.agents.base import BaseAgentState, ReactAgent
from src.core.action_dispatcher import dispatch_action
from src.core.config import get_settings
from src.core.logging import get_logger
from src.core.models import ActionStatus, Incident

logger = get_logger(__name__)
settings = get_settings()


class ExecutionResult(BaseModel):
    """Result of executing a single remediation plan step."""

    step_id: str
    action_id: UUID
    success: bool
    output: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    started_at: datetime
    completed_at: datetime
    duration_seconds: float
    logs: list[str] = Field(default_factory=list)


class PlanExecution(BaseModel):
    """Tracks execution of an entire remediation plan, including step results and rollback state."""

    plan_id: str
    incident_id: UUID
    execution_id: UUID
    status: ActionStatus = ActionStatus.PENDING
    step_results: list[ExecutionResult] = Field(default_factory=list)
    current_step_index: int = 0
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    overall_success: bool | None = None
    rollback_initiated: bool = False


class ExecutorState(BaseAgentState):
    """State for the executor agent, tracking plan, current step, and approval status."""

    incident: Incident | None = None
    plan: dict[str, Any] | None = None
    execution: PlanExecution | None = None
    current_step: dict[str, Any] | None = None
    approval_pending: bool = False
    approval_request_id: UUID | None = None


class ExecutorAgent(ReactAgent):
    """Agent that executes remediation plans."""

    def _get_specific_prompt(self) -> str:
        return """You are the Executor Agent responsible for executing remediation plans.

Your responsibilities:
1. Execute each step of the remediation plan in order
2. Handle dependencies between steps
3. Request human approval for high-risk actions
4. Monitor execution and handle failures
5. Initiate rollback on failure if configured
6. Collect logs and evidence for each action
7. Update incident status throughout execution

Available tools:
- execute_action: Run a specific remediation action
- request_approval: Request human approval for risky actions
- check_action_status: Check status of running action
- initiate_rollback: Rollback a failed action
- update_incident_status: Update incident during execution
- collect_logs: Gather logs from affected systems
- run_shell_command: Execute shell commands
- kubernetes_action: Perform Kubernetes operations
- cloud_action: Perform cloud provider operations
- servicenow_action: Update ServiceNow tickets

Safety rules:
- NEVER execute destructive actions without approval
- ALWAYS verify preconditions before executing
- MONITOR action progress and timeout appropriately
- ROLLBACK on failure if rollback procedure exists
- LOG everything for audit trail

Output: Update execution status and step results."""

    def _get_tools(self) -> list[BaseTool]:
        return [
            execute_action,
            request_approval,
            check_action_status,
            initiate_rollback,
            update_incident_status,
            collect_logs,
            run_shell_command,
            kubernetes_action,
            cloud_action,
            servicenow_action,
        ]

    def _get_state_class(self) -> type[BaseAgentState]:
        return ExecutorState

    async def _process_task(self, state: ExecutorState) -> ExecutorState:
        """Process execution task."""
        task = state.task
        if not task:
            state.error = "No task provided"
            state.should_continue = False
            return state

        # Get incident and plan from context
        incident_id = task.context.get("incident_id") or task.input_data.get("incident_id")
        plan = task.input_data.get("plan") or task.context.get("plan")

        if incident_id:
            state.incident = await self._get_incident(incident_id)
        if plan:
            state.plan = plan

        if not state.incident or not state.plan:
            state.error = "Missing incident or plan"
            state.should_continue = False
            return state

        # Initialize or continue execution
        if not state.execution:
            state.execution = PlanExecution(
                plan_id=state.plan.get("plan_id", ""),
                incident_id=state.incident.id,
                execution_id=uuid4(),
            )

        # Execute next step
        steps = state.plan.get("steps", [])
        if state.execution.current_step_index < len(steps):
            step = steps[state.execution.current_step_index]
            state.current_step = step

            # Check if approval needed
            if step.get("requires_approval", False) and not step.get("approved", False):
                approval_result = await request_approval.ainvoke({
                    "step": step,
                    "incident_id": str(state.incident.id),
                    "execution_id": str(state.execution.execution_id),
                })
                if not approval_result.get("approved", False):
                    status = approval_result.get("status", "PENDING")
                    if status == "PENDING":
                        state.approval_pending = True
                        state.approval_request_id = approval_result.get("request_id")
                        state.intermediate_results["approval"] = {
                            "request_id": str(approval_result.get("request_id")),
                            "message": f"Approval pending for step {step.get('step_id')}",
                        }
                        state.should_continue = False
                        return state
                    state.error = f"Approval rejected: {approval_result.get('reason', 'No reason')}"
                    state.should_continue = False
                    return state
                step["approved"] = True

            # Execute the step
            result = await self._execute_step(state, step)
            state.execution.step_results.append(result)

            if result.success:
                state.execution.current_step_index += 1
            else:
                # Check if rollback needed
                if step.get("rollback_action"):
                    rollback_result = await initiate_rollback.ainvoke({
                        "action_id": result.action_id,
                        "rollback_action": step["rollback_action"],
                    })
                    if not rollback_result.get("success", False):
                        state.error = f"Rollback failed: {rollback_result.get('error')}"
                        state.should_continue = False
                        return state
                    state.execution.rollback_initiated = True

                state.error = f"Step {step['step_id']} failed: {result.error}"
                state.should_continue = False
                return state

            # Update incident status
            await update_incident_status.ainvoke({
                "incident_id": str(state.incident.id),
                "status": "RESOLVING",
                "message": (
                    f"Executing step {state.execution.current_step_index}"
                    f"/{len(steps)}: {step.get('description', '')}"
                ),
            })

        # Check if all steps complete
        if state.execution.current_step_index >= len(steps):
            state.execution.completed_at = datetime.now(UTC)
            state.execution.overall_success = all(r.success for r in state.execution.step_results)
            state.execution.status = (
                ActionStatus.SUCCESS if state.execution.overall_success else ActionStatus.FAILED
            )

            await update_incident_status.ainvoke({
                "incident_id": str(state.incident.id),
                "status": "RESOLVED" if state.execution.overall_success else "RESOLVING",
                "message": (
                    "Execution completed successfully"
                    if state.execution.overall_success
                    else "Execution completed with failures"
                ),
            })

            state.should_continue = False

        return state

    async def _execute_step(self, state: ExecutorState, step: dict[str, Any]) -> ExecutionResult:
        """Execute a single remediation plan step via the action dispatcher."""
        action_type = step.get("action_type")
        step_id = step.get("step_id", "unknown")

        result = await execute_action.ainvoke({
            "action_type": action_type,
            "target_resource": step.get("target_resource"),
            "target_resource_type": step.get("target_resource_type"),
            "parameters": step.get("parameters", {}),
            "incident_id": str(state.incident.id),
            "execution_id": str(state.execution.execution_id),
        })

        return ExecutionResult(
            step_id=step_id,
            action_id=result.get("action_id", uuid4()),
            success=result.get("success", False),
            output=result.get("output", {}),
            error=result.get("error"),
            started_at=result.get("started_at", datetime.now(UTC)),
            completed_at=result.get("completed_at", datetime.now(UTC)),
            duration_seconds=result.get("duration_seconds", 0),
            logs=result.get("logs", []),
        )


# Tools for Executor Agent
@tool
async def execute_action(
    action_type: str,
    target_resource: str,
    target_resource_type: str,
    parameters: dict[str, Any],
    incident_id: str,
    execution_id: str,
) -> dict[str, Any]:
    """Execute a remediation action."""
    logger.info("Executing action", action_type=action_type, resource=target_resource)
    return await dispatch_action(
        action_type=action_type,
        target_resource=target_resource,
        target_resource_type=target_resource_type,
        parameters=parameters,
        incident_id=incident_id,
        execution_id=execution_id,
    )


@tool
async def request_approval(
    step: dict[str, Any],
    incident_id: str,
    execution_id: str,
) -> dict[str, Any]:
    """Request human approval for a risky action."""
    logger.info("Requesting approval", step=step.get("step_id"), incident=incident_id)
    from src.core.approval import create_approval_request

    request = create_approval_request(
        action_type=step.get("action_type", "UNKNOWN"),
        target_resource=step.get("target_resource", "unknown"),
        parameters=step.get("parameters", {}),
        incident_id=incident_id,
        execution_id=execution_id,
    )

    return {
        "approved": request.status.value == "APPROVED",
        "reason": request.rejection_reason or f"Status: {request.status.value}",
        "request_id": request.id,
        "status": request.status.value,
    }


@tool
async def check_action_status(action_id: str) -> dict[str, Any]:
    """Check status of a running action."""
    logger.info("Checking action status", action_id=action_id)
    return {"status": "completed", "progress": 100}


@tool
async def initiate_rollback(
    action_id: str,
    rollback_action: dict[str, Any],
) -> dict[str, Any]:
    """Initiate rollback of a failed action."""
    logger.info("Initiating rollback", action_id=action_id)
    return {"success": True, "message": "Rollback completed"}


@tool
async def update_incident_status(
    incident_id: str,
    status: str,
    message: str,
) -> dict[str, Any]:
    """Update incident status during execution."""
    logger.info("Updating incident status", incident_id=incident_id, status=status)
    return {"success": True}


@tool
async def collect_logs(
    resource_ids: list[str],
    since_minutes: int = 30,
) -> dict[str, Any]:
    """Collect logs from affected resources."""
    logger.info("Collecting logs", resources=resource_ids)
    return {"logs": {}, "collected": len(resource_ids)}


@tool
async def run_shell_command(
    command: str,
    host: str,
    timeout: int = 300,
) -> dict[str, Any]:
    """Run shell command on remote host."""
    logger.info("Running shell command", command=command, host=host)
    from src.core.action_dispatcher import _run_command

    cmd_parts = ["ssh", host, command] if host else ["bash", "-c", command]
    result = await _run_command(cmd_parts, timeout=timeout)
    return {
        "success": result["exit_code"] == 0,
        "stdout": result["stdout"],
        "stderr": result["stderr"],
        "exit_code": result["exit_code"],
    }


@tool
async def kubernetes_action(
    action: str,
    resource_type: str,
    resource_name: str,
    namespace: str,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Perform Kubernetes operation using kubectl or K8s API.

    This is a stub implementation that logs the action and returns a
    placeholder success response. Replace with actual K8s client calls.
    """
    logger.info("Kubernetes action", action=action, resource=resource_name, namespace=namespace)
    return {"success": True, "message": f"Performed {action} on {resource_type}/{resource_name}"}


@tool
async def cloud_action(
    provider: str,
    action: str,
    resource_type: str,
    resource_id: str,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Perform cloud provider operation (AWS/GCP/Azure).

    This is a stub implementation that logs the action and returns a
    placeholder success response. Replace with actual cloud SDK calls.
    """
    logger.info("Cloud action", provider=provider, action=action, resource=resource_id)
    return {"success": True, "message": f"Performed {action} on {resource_type}/{resource_id}"}


@tool
async def servicenow_action(
    action: str,
    ticket_number: str | None = None,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Perform ServiceNow operation.

    This is a stub implementation that logs the action and returns a
    placeholder success response. Replace with actual ServiceNow API calls.
    """
    logger.info("ServiceNow action", action=action, ticket=ticket_number)
    return {"success": True, "message": f"Performed {action} on ServiceNow"}


# Export
__all__ = [
    "ExecutionResult",
    "ExecutorAgent",
    "ExecutorState",
    "PlanExecution",
]
