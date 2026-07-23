"""Agent execution endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.agents.base import AgentType, get_agent
from src.core.models import AgentTask
from src.core.utils import enum_val

router = APIRouter()


class AgentExecuteRequest(BaseModel):
    """Request to execute an agent task."""

    agent_type: AgentType
    task_type: str
    input_data: dict[str, Any] = Field(default_factory=dict)
    context: dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=5, ge=1, le=10)
    timeout_seconds: int = Field(default=300, ge=1)


class AgentExecuteResponse(BaseModel):
    """Response from executing an agent task."""

    task_id: str
    agent_type: str
    success: bool
    output: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    execution_time_ms: int = 0
    confidence_score: float = 0.0


@router.post("/execute", response_model=AgentExecuteResponse)
async def execute_agent(req: AgentExecuteRequest) -> AgentExecuteResponse:
    """Execute an agent task."""
    try:
        agent = get_agent(req.agent_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    task = AgentTask(
        agent_type=req.agent_type,
        task_type=req.task_type,
        input_data=req.input_data,
        context=req.context,
        priority=req.priority,
        timeout_seconds=req.timeout_seconds,
    )

    result = await agent.execute(task)

    return AgentExecuteResponse(
        task_id=str(result.task_id),
        agent_type=enum_val(result.agent_type),
        success=result.success,
        output=result.output,
        error=result.error,
        execution_time_ms=result.execution_time_ms,
        confidence_score=result.confidence_score,
    )


@router.get("/types")
async def list_agent_types() -> list[str]:
    """List all available agent types."""
    return [enum_val(t) for t in AgentType]


@router.get("/{agent_type}/health")
async def agent_health(agent_type: AgentType) -> dict[str, Any]:
    """Check health of a specific agent."""
    try:
        agent = get_agent(agent_type)
        return await agent.health_check()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
