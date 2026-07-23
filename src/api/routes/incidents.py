"""Incident management endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.core.incident_store import get_incident, list_incidents, save_incident
from src.core.models import (
    Incident,
    IncidentCategory,
    IncidentSeverity,
    IncidentStatus,
    TicketPriority,
)
from src.core.similar_incidents import find_similar, index_incident
from src.core.utils import enum_val

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

class IncidentCreateRequest(BaseModel):
    """Request to create a new incident."""

    title: str
    description: str
    severity: IncidentSeverity = IncidentSeverity.SEV3
    category: IncidentCategory = IncidentCategory.UNKNOWN
    priority: TicketPriority = TicketPriority.P3
    source: str = "api"
    source_id: str | None = None
    affected_services: list[str] = Field(default_factory=list)
    affected_resources: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class IncidentUpdateRequest(BaseModel):
    """Request to update an incident's mutable fields."""

    status: IncidentStatus | None = None
    severity: IncidentSeverity | None = None
    root_cause: str | None = None
    resolution: str | None = None
    assigned_to: str | None = None
    assigned_team: str | None = None
    tags: list[str] | None = None


class IncidentResponse(BaseModel):
    """Incident response schema returned by the API."""

    id: str
    title: str
    description: str
    severity: str
    status: str
    category: str
    priority: str
    source: str
    affected_services: list[str]
    affected_resources: list[str]
    created_at: str
    root_cause: str | None = None
    resolution: str | None = None


def _incident_to_response(inc: Incident) -> IncidentResponse:
    """Convert an Incident domain model to the API response schema."""
    return IncidentResponse(
        id=str(inc.id),
        title=inc.title,
        description=inc.description,
        severity=enum_val(inc.severity),
        status=enum_val(inc.status),
        category=enum_val(inc.category),
        priority=enum_val(inc.priority),
        source=inc.source,
        affected_services=inc.affected_services,
        affected_resources=inc.affected_resources,
        created_at=inc.created_at.isoformat(),
        root_cause=inc.root_cause,
        resolution=inc.resolution,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=list[IncidentResponse])
async def list_all_incidents() -> list[IncidentResponse]:
    """Return all known incidents."""
    return [_incident_to_response(i) for i in list_incidents()]


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident_by_id(incident_id: str) -> IncidentResponse:
    """Return a single incident."""
    inc = get_incident(incident_id)
    if inc is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return _incident_to_response(inc)


@router.post("", response_model=IncidentResponse, status_code=201)
async def create_incident(req: IncidentCreateRequest) -> IncidentResponse:
    """Create a new incident."""
    inc = Incident(
        title=req.title,
        description=req.description,
        severity=req.severity,
        status=IncidentStatus.OPEN,
        category=req.category,
        priority=req.priority,
        source=req.source,
        source_id=req.source_id,
        affected_services=req.affected_services,
        affected_resources=req.affected_resources,
        tags=req.tags,
    )
    saved = save_incident(inc)
    await index_incident(saved)
    return _incident_to_response(saved)


@router.patch("/{incident_id}", response_model=IncidentResponse)
async def update_incident(incident_id: str, req: IncidentUpdateRequest) -> IncidentResponse:
    """Update an existing incident."""
    inc = get_incident(incident_id)
    if inc is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    if req.status is not None:
        inc.status = req.status
    if req.severity is not None:
        inc.severity = req.severity
    if req.root_cause is not None:
        inc.root_cause = req.root_cause
    if req.resolution is not None:
        inc.resolution = req.resolution
    if req.assigned_to is not None:
        inc.assigned_to = req.assigned_to
    if req.assigned_team is not None:
        inc.assigned_team = req.assigned_team
    if req.tags is not None:
        inc.tags = req.tags

    saved = save_incident(inc)
    return _incident_to_response(saved)


@router.get("/{incident_id}/similar")
async def get_similar_incidents(incident_id: str, limit: int = 5) -> list[dict[str, Any]]:
    """Find incidents similar to the given one."""
    inc = get_incident(incident_id)
    if inc is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return await find_similar(inc, limit=limit)
