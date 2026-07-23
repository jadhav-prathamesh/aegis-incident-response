"""Core domain models for the platform."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: str,
        },
    )


class TimestampMixin(BaseModel):
    """Mixin for created/updated timestamps."""

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class IDMixin(BaseModel):
    """Mixin for UUID primary key."""

    id: UUID = Field(default_factory=uuid4)


# Enums
class IncidentSeverity(StrEnum):
    """Incident severity levels."""

    SEV1 = "SEV1"  # Critical - system down, data loss
    SEV2 = "SEV2"  # High - major functionality impacted
    SEV3 = "SEV3"  # Medium - minor functionality impacted
    SEV4 = "SEV4"  # Low - cosmetic issue, no user impact
    SEV5 = "SEV5"  # Informational - monitoring alert, no action needed


class IncidentStatus(StrEnum):
    """Incident lifecycle status."""

    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    INVESTIGATING = "INVESTIGATING"
    IDENTIFIED = "IDENTIFIED"
    RESOLVING = "RESOLVING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class IncidentCategory(StrEnum):
    """Incident categories."""

    INFRASTRUCTURE = "INFRASTRUCTURE"
    APPLICATION = "APPLICATION"
    DATABASE = "DATABASE"
    NETWORK = "NETWORK"
    SECURITY = "SECURITY"
    PERFORMANCE = "PERFORMANCE"
    CAPACITY = "CAPACITY"
    DEPLOYMENT = "DEPLOYMENT"
    CONFIGURATION = "CONFIGURATION"
    EXTERNAL = "EXTERNAL"
    UNKNOWN = "UNKNOWN"


class AgentType(StrEnum):
    """Types of AI agents in the system."""

    ORCHESTRATOR = "ORCHESTRATOR"
    PLANNER = "PLANNER"
    EXECUTOR = "EXECUTOR"
    OBSERVER = "OBSERVER"
    VALIDATOR = "VALIDATOR"
    RCA_ANALYZER = "RCA_ANALYZER"
    HEALING_AGENT = "HEALING_AGENT"
    TICKET_ROUTER = "TICKET_ROUTER"
    PRIORITIZER = "PRIORITIZER"
    PREDICTOR = "PREDICTOR"


class ActionStatus(StrEnum):
    """Action execution status."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTING = "EXECUTING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"


class TicketPriority(StrEnum):
    """Ticket priority levels."""

    P1 = "P1"  # Critical - immediate response
    P2 = "P2"  # High - 1 hour response
    P3 = "P3"  # Medium - 4 hour response
    P4 = "P4"  # Low - 24 hour response
    P5 = "P5"  # Planning - scheduled


class ResourceType(StrEnum):
    """Types of infrastructure resources."""

    VM = "VM"
    CONTAINER = "CONTAINER"
    DATABASE = "DATABASE"
    LOAD_BALANCER = "LOAD_BALANCER"
    NETWORK = "NETWORK"
    STORAGE = "STORAGE"
    KUBERNETES_CLUSTER = "KUBERNETES_CLUSTER"
    KUBERNETES_NODE = "KUBERNETES_NODE"
    KUBERNETES_POD = "KUBERNETES_POD"
    SERVERLESS = "SERVERLESS"
    MESSAGE_QUEUE = "MESSAGE_QUEUE"
    CACHE = "CACHE"
    CDN = "CDN"
    DNS = "DNS"
    FIREWALL = "FIREWALL"
    MONITORING = "MONITORING"
    LOGGING = "LOGGING"


# Agent communication models
class AgentTask(BaseSchema):
    """Task assigned to an agent."""

    task_id: UUID = Field(default_factory=uuid4)
    agent_type: AgentType
    task_type: str
    input_data: dict[str, Any]
    context: dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=5, ge=1, le=10)
    timeout_seconds: int = Field(default=300, ge=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    status: str = "IDLE"
    result: dict[str, Any] | None = None
    error: str | None = None


class AgentResult(BaseSchema):
    """Result from agent execution."""

    task_id: UUID
    agent_type: AgentType
    success: bool
    output: dict[str, Any] = Field(default_factory=dict)
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    next_actions: list[AgentTask] = Field(default_factory=list)
    error: str | None = None
    execution_time_ms: int = 0
    tokens_used: int = 0
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)


# Incident models
class Incident(BaseSchema, IDMixin, TimestampMixin):
    """Incident domain model."""

    title: str
    description: str
    severity: IncidentSeverity = IncidentSeverity.SEV3
    status: IncidentStatus = IncidentStatus.OPEN
    category: IncidentCategory = IncidentCategory.UNKNOWN
    priority: TicketPriority = TicketPriority.P3

    # Source information
    source: str  # monitoring tool, alert name, etc.
    source_id: str | None = None
    affected_services: list[str] = Field(default_factory=list)
    affected_resources: list[str] = Field(default_factory=list)

    # Assignment
    assigned_to: str | None = None
    assigned_team: str | None = None

    # Timing
    detected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    closed_at: datetime | None = None

    # Root cause
    root_cause: str | None = None
    root_cause_category: IncidentCategory | None = None
    contributing_factors: list[str] = Field(default_factory=list)

    # Resolution
    resolution: str | None = None
    resolution_category: str | None = None
    preventive_actions: list[str] = Field(default_factory=list)

    # Metrics
    mttr_minutes: int | None = None
    impact_duration_minutes: int | None = None
    customer_impact: bool = False
    revenue_impact_usd: float | None = None

    # Related entities
    related_incidents: list[UUID] = Field(default_factory=list)
    parent_incident: UUID | None = None
    child_incidents: list[UUID] = Field(default_factory=list)

    # Tags and metadata
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class IncidentUpdate(BaseSchema):
    """Incident status update."""

    update_id: UUID = Field(default_factory=uuid4)
    incident_id: UUID
    author: str
    status_from: IncidentStatus | None = None
    status_to: IncidentStatus | None = None
    message: str
    is_public: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Alert(BaseSchema, IDMixin, TimestampMixin):
    """Alert from monitoring system."""

    alert_name: str
    severity: IncidentSeverity
    status: str  # firing, resolved, acknowledged
    source: str
    source_id: str
    resource_id: UUID | None = None
    message: str
    description: str | None = None
    labels: dict[str, str] = Field(default_factory=dict)
    annotations: dict[str, str] = Field(default_factory=dict)
    starts_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    ends_at: datetime | None = None
    generator_url: str | None = None
    fingerprint: str | None = None


# Configuration models
class AgentConfig(BaseSchema):
    """Agent configuration."""

    agent_type: AgentType
    enabled: bool = True
    model: str = "nvidia/nemotron-3-ultra-550b-a55b:free"
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1)
    timeout_seconds: int = Field(default=300, ge=1)
    max_retries: int = Field(default=3, ge=0)
    retry_delay_seconds: int = Field(default=5, ge=1)
    system_prompt: str | None = None
    tools: list[str] = Field(default_factory=list)
    memory_enabled: bool = True
    memory_window: int = 10
    custom_config: dict[str, Any] = Field(default_factory=dict)
