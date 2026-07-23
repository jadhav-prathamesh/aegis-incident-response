"""Application configuration management using Pydantic Settings."""

from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration."""

    model_config = SettingsConfigDict(env_prefix="DB_")

    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    username: str = Field(default="postgres")
    password: str = Field(default="postgres")
    database: str = Field(default="agentic_platform")
    pool_size: int = Field(default=20)
    max_overflow: int = Field(default=10)
    pool_timeout: int = Field(default=30)
    pool_recycle: int = Field(default=3600)
    echo: bool = Field(default=False)
    ssl_mode: str = Field(default="prefer")

    @property
    def url(self) -> str:
        """Async database URL for SQLAlchemy."""
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?sslmode={self.ssl_mode}"

    @property
    def sync_url(self) -> str:
        """Synchronous database URL for migrations."""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?sslmode={self.ssl_mode}"


class RedisSettings(BaseSettings):
    """Redis configuration."""

    model_config = SettingsConfigDict(env_prefix="REDIS_")

    host: str = Field(default="localhost")
    port: int = Field(default=6379)
    username: str | None = Field(default=None)
    password: str | None = Field(default=None)
    database: int = Field(default=0)
    max_connections: int = Field(default=50)
    socket_timeout: int = Field(default=5)
    socket_connect_timeout: int = Field(default=5)
    decode_responses: bool = Field(default=True)
    default_ttl: int = Field(default=3600)

    @property
    def url(self) -> str:
        """Redis connection URL."""
        auth = ""
        if self.username and self.password:
            auth = f"{self.username}:{self.password}@"
        elif self.password:
            auth = f":{self.password}@"
        return f"redis://{auth}{self.host}:{self.port}/{self.database}"


class VectorDBSettings(BaseSettings):
    """Vector database configuration."""

    model_config = SettingsConfigDict(env_prefix="VECTOR_DB_")

    provider: str = Field(default="pgvector")  # chroma, pgvector
    embedding_dimension: int = Field(default=4096)
    embedding_model: str = Field(default="text-embedding-3-small")
    collection_name: str = Field(default="knowledge_base")

    # Chroma specific
    chroma_host: str = Field(default="localhost")
    chroma_port: int = Field(default=8000)
    chroma_auth_token: str | None = Field(default=None)
    chroma_ssl: bool = Field(default=False)

    # pgvector specific
    pgvector_table_prefix: str = Field(default="vec_")


class LLMSettings(BaseSettings):
    """LLM provider configuration."""

    model_config = SettingsConfigDict(env_prefix="LLM_")

    provider: str = Field(default="openrouter")  # openrouter, openai, anthropic, ollama
    base_url: str = Field(default="https://openrouter.ai/api/v1")
    api_key: str = Field(default="")
    model: str = Field(default="nvidia/nemotron-3-ultra-550b-a55b:free")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1)
    timeout: int = Field(default=120)
    max_retries: int = Field(default=3)
    retry_delay: float = Field(default=1.0)

    # OpenRouter specific
    openrouter_site_url: str = Field(default="https://app.example.com")
    openrouter_app_name: str = Field(default="Aegis")


class AgentSettings(BaseSettings):
    """Agent configuration."""

    model_config = SettingsConfigDict(env_prefix="AGENT_")

    orchestrator_model: str = Field(default="nvidia/nemotron-3-ultra-550b-a55b:free")
    planner_model: str = Field(default="nvidia/nemotron-3-ultra-550b-a55b:free")
    executor_model: str = Field(default="nvidia/nemotron-3-ultra-550b-a55b:free")
    observer_model: str = Field(default="nvidia/nemotron-3-ultra-550b-a55b:free")
    validator_model: str = Field(default="nvidia/nemotron-3-ultra-550b-a55b:free")
    rca_analyzer_model: str = Field(default="nvidia/nemotron-3-ultra-550b-a55b:free")
    healing_agent_model: str = Field(default="nvidia/nemotron-3-ultra-550b-a55b:free")
    ticket_router_model: str = Field(default="nvidia/nemotron-3-ultra-550b-a55b:free")
    prioritizer_model: str = Field(default="nvidia/nemotron-3-ultra-550b-a55b:free")
    predictor_model: str = Field(default="nvidia/nemotron-3-ultra-550b-a55b:free")

    default_temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    default_max_tokens: int = Field(default=4096, ge=1)
    default_timeout: int = Field(default=300, ge=1)
    max_retries: int = Field(default=3, ge=0)
    retry_delay: float = Field(default=5.0, ge=0.1)

    # Memory settings
    memory_enabled: bool = Field(default=True)
    memory_window: int = Field(default=10, ge=1)
    long_term_memory_enabled: bool = Field(default=True)

    # Tool settings
    enable_shell_tools: bool = Field(default=True)
    enable_k8s_tools: bool = Field(default=True)
    enable_cloud_tools: bool = Field(default=True)
    enable_servicenow_tools: bool = Field(default=True)
    enable_monitoring_tools: bool = Field(default=True)


class SecuritySettings(BaseSettings):
    """Security configuration."""

    model_config = SettingsConfigDict(env_prefix="SECURITY_")

    secret_key: str = Field(default="change-me-in-production")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_days: int = Field(default=7)
    api_key_header: str = Field(default="X-API-Key")

    # Rate limiting
    rate_limit_requests: int = Field(default=100)
    rate_limit_window_seconds: int = Field(default=60)

    # CORS
    cors_origins: list[str] = Field(default=["http://localhost:3000", "http://localhost:8080"])
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: list[str] = Field(default=["*"])
    cors_allow_headers: list[str] = Field(default=["*"])

    # Encryption
    encryption_key: str | None = Field(default=None)

    # Audit
    audit_enabled: bool = Field(default=True)
    audit_log_retention_days: int = Field(default=90)


class MonitoringSettings(BaseSettings):
    """Monitoring and observability configuration."""

    model_config = SettingsConfigDict(env_prefix="MONITORING_")

    # Prometheus
    prometheus_enabled: bool = Field(default=True)
    prometheus_port: int = Field(default=9090)
    prometheus_path: str = Field(default="/metrics")

    # OpenTelemetry
    otel_enabled: bool = Field(default=True)
    otel_service_name: str = Field(default="agentic-platform")
    otel_exporter: str = Field(default="prometheus")  # prometheus, otlp, jaeger
    otel_endpoint: str = Field(default="http://localhost:4317")
    otel_sample_rate: float = Field(default=0.1, ge=0.0, le=1.0)

    # Grafana
    grafana_enabled: bool = Field(default=True)
    grafana_url: str = Field(default="http://localhost:3000")
    grafana_api_key: str | None = Field(default=None)

    # Alerting
    alerting_enabled: bool = Field(default=True)
    alertmanager_url: str = Field(default="http://localhost:9093")
    alert_default_severity: str = Field(default="warning")

    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")  # json, console
    log_correlation_enabled: bool = Field(default=True)


class IntegrationSettings(BaseSettings):
    """External integration configuration."""

    model_config = SettingsConfigDict(env_prefix="INTEGRATION_")

    # ServiceNow
    servicenow_enabled: bool = Field(default=False)
    servicenow_instance: str = Field(default="")
    servicenow_username: str = Field(default="")
    servicenow_password: str = Field(default="")
    servicenow_client_id: str = Field(default="")
    servicenow_client_secret: str = Field(default="")
    servicenow_api_version: str = Field(default="/api/now/table")

    # PagerDuty
    pagerduty_enabled: bool = Field(default=False)
    pagerduty_api_key: str = Field(default="")
    pagerduty_service_id: str = Field(default="")

    # Slack
    slack_enabled: bool = Field(default=False)
    slack_bot_token: str = Field(default="")
    slack_signing_secret: str = Field(default="")
    slack_app_token: str = Field(default="")
    slack_default_channel: str = Field(default="#incidents")

    # Datadog
    datadog_enabled: bool = Field(default=False)
    datadog_api_key: str = Field(default="")
    datadog_app_key: str = Field(default="")
    datadog_site: str = Field(default="datadoghq.com")

    # Prometheus
    prometheus_enabled: bool = Field(default=True)
    prometheus_url: str = Field(default="http://localhost:9090")

    # Grafana
    grafana_enabled: bool = Field(default=True)
    grafana_url: str = Field(default="http://localhost:3000")
    grafana_api_key: str = Field(default="")

    # Kubernetes
    kubernetes_enabled: bool = Field(default=True)
    kubernetes_config_path: str | None = Field(default=None)
    kubernetes_context: str | None = Field(default=None)

    # Cloud providers
    aws_enabled: bool = Field(default=False)
    aws_region: str = Field(default="us-east-1")
    aws_access_key_id: str = Field(default="")
    aws_secret_access_key: str = Field(default="")

    gcp_enabled: bool = Field(default=False)
    gcp_project_id: str = Field(default="")
    gcp_credentials_path: str = Field(default="")

    azure_enabled: bool = Field(default=False)
    azure_subscription_id: str = Field(default="")
    azure_tenant_id: str = Field(default="")
    azure_client_id: str = Field(default="")
    azure_client_secret: str = Field(default="")


class KubernetesSettings(BaseSettings):
    """Kubernetes deployment configuration."""

    model_config = SettingsConfigDict(env_prefix="K8S_")

    namespace: str = Field(default="agentic-platform")
    replicas: int = Field(default=3)
    resources_limits_cpu: str = Field(default="2000m")
    resources_limits_memory: str = Field(default="4Gi")
    resources_requests_cpu: str = Field(default="500m")
    resources_requests_memory: str = Field(default="1Gi")

    # Autoscaling
    hpa_enabled: bool = Field(default=True)
    hpa_min_replicas: int = Field(default=3)
    hpa_max_replicas: int = Field(default=20)
    hpa_target_cpu_utilization: int = Field(default=70)
    hpa_target_memory_utilization: int = Field(default=80)

    # Ingress
    ingress_enabled: bool = Field(default=True)
    ingress_host: str = Field(default="app.example.com")
    ingress_tls_enabled: bool = Field(default=True)
    ingress_cert_manager: bool = Field(default=True)

    # Service mesh
    istio_enabled: bool = Field(default=False)
    linkerd_enabled: bool = Field(default=False)

    # Monitoring
    servicemonitor_enabled: bool = Field(default=True)
    podmonitor_enabled: bool = Field(default=True)


class StorageSettings(BaseSettings):
    """Storage configuration."""

    model_config = SettingsConfigDict(env_prefix="STORAGE_")

    # Object storage
    s3_enabled: bool = Field(default=False)
    s3_endpoint: str = Field(default="")
    s3_bucket: str = Field(default="")
    s3_access_key: str = Field(default="")
    s3_secret_key: str = Field(default="")
    s3_region: str = Field(default="us-east-1")

    # Local storage
    local_storage_path: str = Field(default="/data")
    max_local_storage_gb: int = Field(default=100)

    # Backup
    backup_enabled: bool = Field(default=True)
    backup_schedule: str = Field(default="0 2 * * *")  # Daily at 2 AM
    backup_retention_days: int = Field(default=30)
    backup_storage: str = Field(default="s3")  # s3, local


class FeatureFlagsSettings(BaseSettings):
    """Feature flags for gradual rollouts."""

    model_config = SettingsConfigDict(env_prefix="FEATURE_")

    enable_self_healing: bool = Field(default=True)
    enable_predictive_failure: bool = Field(default=True)
    enable_rca_analysis: bool = Field(default=True)
    enable_intelligent_routing: bool = Field(default=True)
    enable_incident_prioritization: bool = Field(default=True)
    enable_knowledge_base: bool = Field(default=True)
    enable_multi_agent_orchestration: bool = Field(default=True)
    enable_human_in_loop: bool = Field(default=True)
    enable_audit_logging: bool = Field(default=True)
    enable_cost_optimization: bool = Field(default=False)
    enable_chaos_engineering: bool = Field(default=False)
    enable_gitops: bool = Field(default=False)


class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="Aegis")
    app_version: str = Field(default="1.0.0")
    environment: str = Field(default="development")  # development, staging, production
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")
    api_prefix: str = Field(default="/api/v1")
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    workers: int = Field(default=4)

    # Sub-configurations
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    vector_db: VectorDBSettings = Field(default_factory=VectorDBSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    agent: AgentSettings = Field(default_factory=AgentSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    integration: IntegrationSettings = Field(default_factory=IntegrationSettings)
    kubernetes: KubernetesSettings = Field(default_factory=KubernetesSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    features: FeatureFlagsSettings = Field(default_factory=FeatureFlagsSettings)

    @field_validator("database", mode="before")
    @classmethod
    def _validate_database(cls, v: Any) -> DatabaseSettings:
        if isinstance(v, DatabaseSettings):
            return v
        if isinstance(v, dict):
            return DatabaseSettings(**v)
        return DatabaseSettings()

    @field_validator("redis", mode="before")
    @classmethod
    def _validate_redis(cls, v: Any) -> RedisSettings:
        if isinstance(v, RedisSettings):
            return v
        if isinstance(v, dict):
            return RedisSettings(**v)
        return RedisSettings()

    @field_validator("vector_db", mode="before")
    @classmethod
    def _validate_vector_db(cls, v: Any) -> VectorDBSettings:
        if isinstance(v, VectorDBSettings):
            return v
        if isinstance(v, dict):
            return VectorDBSettings(**v)
        return VectorDBSettings()

    @field_validator("llm", mode="before")
    @classmethod
    def _validate_llm(cls, v: Any) -> LLMSettings:
        if isinstance(v, LLMSettings):
            return v
        if isinstance(v, dict):
            return LLMSettings(**v)
        return LLMSettings()

    @field_validator("agent", mode="before")
    @classmethod
    def _validate_agent(cls, v: Any) -> AgentSettings:
        if isinstance(v, AgentSettings):
            return v
        if isinstance(v, dict):
            return AgentSettings(**v)
        return AgentSettings()

    @field_validator("security", mode="before")
    @classmethod
    def _validate_security(cls, v: Any) -> SecuritySettings:
        if isinstance(v, SecuritySettings):
            return v
        if isinstance(v, dict):
            return SecuritySettings(**v)
        return SecuritySettings()

    @field_validator("monitoring", mode="before")
    @classmethod
    def _validate_monitoring(cls, v: Any) -> MonitoringSettings:
        if isinstance(v, MonitoringSettings):
            return v
        if isinstance(v, dict):
            return MonitoringSettings(**v)
        return MonitoringSettings()

    @field_validator("integration", mode="before")
    @classmethod
    def _validate_integration(cls, v: Any) -> IntegrationSettings:
        if isinstance(v, IntegrationSettings):
            return v
        if isinstance(v, dict):
            return IntegrationSettings(**v)
        return IntegrationSettings()

    @field_validator("kubernetes", mode="before")
    @classmethod
    def _validate_kubernetes(cls, v: Any) -> KubernetesSettings:
        if isinstance(v, KubernetesSettings):
            return v
        if isinstance(v, dict):
            return KubernetesSettings(**v)
        return KubernetesSettings()

    @field_validator("storage", mode="before")
    @classmethod
    def _validate_storage(cls, v: Any) -> StorageSettings:
        if isinstance(v, StorageSettings):
            return v
        if isinstance(v, dict):
            return StorageSettings(**v)
        return StorageSettings()

    @field_validator("features", mode="before")
    @classmethod
    def _validate_features(cls, v: Any) -> FeatureFlagsSettings:
        if isinstance(v, FeatureFlagsSettings):
            return v
        if isinstance(v, dict):
            return FeatureFlagsSettings(**v)
        return FeatureFlagsSettings()

    @field_validator("debug", mode="before")
    @classmethod
    def normalize_debug(cls, value: Any) -> Any:
        """Handle non-boolean DEBUG values inherited from shell environments."""
        if isinstance(value, str) and value.lower() in {"release", "production", "prod"}:
            return False
        return value


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
