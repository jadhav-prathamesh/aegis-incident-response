"""Custom exceptions for the platform."""

from typing import Any


class PlatformException(Exception):
    """Base exception for the platform."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        details: dict[str, Any] | None = None,
        status_code: int = 500,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.status_code = status_code

    def to_dict(self) -> dict[str, Any]:
        """Serialize exception to a dictionary for API responses."""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


class ConfigurationError(PlatformException):
    """Configuration related errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, "CONFIGURATION_ERROR", details, 500)


class AuthenticationError(PlatformException):
    """Authentication errors."""

    def __init__(
        self, message: str = "Authentication failed",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, "AUTHENTICATION_ERROR", details, 401)


class AuthorizationError(PlatformException):
    """Authorization errors."""

    def __init__(
        self, message: str = "Insufficient permissions",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, "AUTHORIZATION_ERROR", details, 403)


class ValidationError(PlatformException):
    """Input validation errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, "VALIDATION_ERROR", details, 422)


class NotFoundError(PlatformException):
    """Resource not found errors."""

    def __init__(self, resource: str, identifier: str, details: dict[str, Any] | None = None):
        super().__init__(
            f"{resource} not found: {identifier}",
            "NOT_FOUND",
            (
                {**details, "resource": resource, "identifier": identifier}
                if details
                else {"resource": resource, "identifier": identifier}
            ),
            404,
        )


class ConflictError(PlatformException):
    """Resource conflict errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, "CONFLICT", details, 409)


class RateLimitError(PlatformException):
    """Rate limit exceeded errors."""

    def __init__(self, message: str = "Rate limit exceeded", details: dict[str, Any] | None = None):
        super().__init__(message, "RATE_LIMIT_EXCEEDED", details, 429)


class ExternalServiceError(PlatformException):
    """External service integration errors."""

    def __init__(
        self,
        service: str,
        message: str,
        details: dict[str, Any] | None = None,
        status_code: int = 502,
    ):
        super().__init__(
            f"{service} error: {message}",
            "EXTERNAL_SERVICE_ERROR",
            {**details, "service": service} if details else {"service": service},
            status_code,
        )


class DatabaseError(PlatformException):
    """Database operation errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, "DATABASE_ERROR", details, 500)


class CacheError(PlatformException):
    """Cache operation errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, "CACHE_ERROR", details, 500)


class VectorDBError(PlatformException):
    """Vector database operation errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, "VECTOR_DB_ERROR", details, 500)


class LLMError(PlatformException):
    """LLM provider errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, "LLM_ERROR", details, 500)


class AgentError(PlatformException):
    """Agent execution errors."""

    def __init__(
        self,
        agent_type: str,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            f"Agent {agent_type} error: {message}",
            "AGENT_ERROR",
            {**details, "agent_type": agent_type} if details else {"agent_type": agent_type},
            500,
        )


class OrchestrationError(PlatformException):
    """Multi-agent orchestration errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, "ORCHESTRATION_ERROR", details, 500)


class AgentTimeoutError(AgentError):
    """Agent execution timeout."""

    def __init__(self, agent_type: str, timeout_seconds: int):
        super().__init__(
            agent_type,
            f"Agent timed out after {timeout_seconds} seconds",
            {"timeout_seconds": timeout_seconds},
        )


class AgentMaxRetriesError(AgentError):
    """Agent exceeded maximum retries."""

    def __init__(self, agent_type: str, max_retries: int):
        super().__init__(
            agent_type,
            f"Agent exceeded maximum retries ({max_retries})",
            {"max_retries": max_retries},
        )


class ApprovalRequiredError(PlatformException):
    """Action requires human approval."""

    def __init__(self, action_id: str, message: str = "Action requires human approval"):
        super().__init__(
            message,
            "APPROVAL_REQUIRED",
            {"action_id": action_id},
            409,
        )


class ApprovalRejectedError(PlatformException):
    """Action approval was rejected."""

    def __init__(self, action_id: str, reason: str):
        super().__init__(
            f"Action approval rejected: {reason}",
            "APPROVAL_REJECTED",
            {"action_id": action_id, "reason": reason},
            409,
        )


class SelfHealingError(PlatformException):
    """Self-healing operation errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, "SELF_HEALING_ERROR", details, 500)


class RollbackError(PlatformException):
    """Rollback operation errors."""

    def __init__(self, action_id: str, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            f"Rollback failed for action {action_id}: {message}",
            "ROLLBACK_ERROR",
            {**details, "action_id": action_id} if details else {"action_id": action_id},
            500,
        )


class KnowledgeBaseError(PlatformException):
    """Knowledge base operation errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, "KNOWLEDGE_BASE_ERROR", details, 500)


class RCAError(PlatformException):
    """Root cause analysis errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, "RCA_ERROR", details, 500)


class PredictionError(PlatformException):
    """Predictive failure detection errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, "PREDICTION_ERROR", details, 500)


class IntegrationError(PlatformException):
    """Integration configuration or runtime errors."""

    def __init__(self, integration: str, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            f"Integration {integration} error: {message}",
            "INTEGRATION_ERROR",
            {**details, "integration": integration} if details else {"integration": integration},
            500,
        )


class KubernetesError(PlatformException):
    """Kubernetes operation errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, "KUBERNETES_ERROR", details, 500)


class CloudProviderError(PlatformException):
    """Cloud provider API errors."""

    def __init__(self, provider: str, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            f"{provider} error: {message}",
            "CLOUD_PROVIDER_ERROR",
            {**details, "provider": provider} if details else {"provider": provider},
            500,
        )


class ResourceNotFoundError(NotFoundError):
    """Infrastructure resource not found."""

    def __init__(self, resource_type: str, identifier: str):
        super().__init__("Resource", identifier, {"resource_type": resource_type})


class DeploymentError(PlatformException):
    """Deployment operation errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, "DEPLOYMENT_ERROR", details, 500)


class TicketError(PlatformException):
    """Ticket management errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, "TICKET_ERROR", details, 500)


class MonitoringError(PlatformException):
    """Monitoring system errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, "MONITORING_ERROR", details, 500)
