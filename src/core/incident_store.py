"""Lightweight incident repository used until persistent storage is wired in."""

from uuid import UUID

from src.core.models import Incident

_incidents: dict[UUID, Incident] = {}


def save_incident(incident: Incident) -> Incident:
    """Store or replace an incident in memory."""
    _incidents[incident.id] = incident
    return incident


def get_incident(incident_id: UUID | str) -> Incident | None:
    """Fetch an incident by UUID."""
    try:
        normalized_id = incident_id if isinstance(incident_id, UUID) else UUID(str(incident_id))
    except ValueError:
        return None
    return _incidents.get(normalized_id)


def list_incidents() -> list[Incident]:
    """Return all known in-memory incidents."""
    return list(_incidents.values())
