# Aegis — "Multi-Agent AI Incident Response Platform"
## Component Reference

## Purpose

Detailed reference for every significant class, function, and module in the codebase.

## Source Traceability

All files under `src/`.

---

## Core Modules

### `src/core/models.py` — Domain Models

| Class | Type | Purpose |
|---|---|---|
| `BaseSchema` | BaseModel | Common config: populate_by_name, use_enum_values, json_encoders |
| `TimestampMixin` | Mixin | created_at, updated_at fields |
| `IDMixin` | Mixin | UUID id field |
| `IncidentSeverity` | StrEnum | SEV1-SEV5 |
| `IncidentStatus` | StrEnum | OPEN → CLOSED lifecycle |
| `IncidentCategory` | StrEnum | INFRASTRUCTURE, APPLICATION, DATABASE, etc. |
| `AgentType` | StrEnum | ORCHESTRATOR, PLANNER, etc. |
| `ActionStatus` | StrEnum | PENDING → ROLLED_BACK |
| `ResourceType` | StrEnum | VM, CONTAINER, DATABASE, etc. |
| `AgentTask` | BaseSchema | Task message for agents |
| `AgentResult` | BaseSchema | Result message from agents |
| `Incident` | BaseSchema+Mixins | Full incident domain object |
| `IncidentUpdate` | BaseSchema | Incident status update |
| `Alert` | BaseSchema+Mixins | Monitoring alert |
| `AgentConfig` | BaseSchema | Agent configuration |

### `src/core/exceptions.py` — Exception Hierarchy

| Exception | Parent | HTTP Code | Purpose |
|---|---|---|---|
| `PlatformException` | Exception | 500 | Base exception |
| `ConfigurationError` | PlatformException | 500 | Config errors |
| `AuthenticationError` | PlatformException | 401 | Auth failures |
| `AuthorizationError` | PlatformException | 403 | Permission failures |
| `ValidationError` | PlatformException | 422 | Input validation |
| `NotFoundError` | PlatformException | 404 | Resource not found |
| `ConflictError` | PlatformException | 409 | Resource conflicts |
| `RateLimitError` | PlatformException | 429 | Rate limiting |
| `ExternalServiceError` | PlatformException | 502 | External service failure |
| `DatabaseError` | PlatformException | 500 | DB operation errors |
| `CacheError` | PlatformException | 500 | Cache errors |
| `VectorDBError` | PlatformException | 500 | Vector DB errors |
| `LLMError` | PlatformException | 500 | LLM provider errors |
| `AgentError` | PlatformException | 500 | Agent execution errors |
| `OrchestrationError` | PlatformException | 500 | Orchestration errors |
| `AgentTimeoutError` | AgentError | 500 | Agent timeout |
| `AgentMaxRetriesError` | AgentError | 500 | Max retries exceeded |
| `ApprovalRequiredError` | PlatformException | 409 | Human approval needed |
| `ApprovalRejectedError` | PlatformException | 409 | Approval rejected |
| `SelfHealingError` | PlatformException | 500 | Self-healing failures |
| `RollbackError` | PlatformException | 500 | Rollback failures |
| `KnowledgeBaseError` | PlatformException | 500 | KB errors |
| `RCAError` | PlatformException | 500 | RCA errors |
| `ResourceNotFoundError` | NotFoundError | 404 | Infra resource not found |

### `src/core/config.py` — Settings

11 settings classes with pydantic-settings. See `08_Configuration.md` for full reference.

### `src/core/database.py` — Database

| Symbol | Purpose |
|---|---|
| `Base` | SQLAlchemy DeclarativeBase |
| `engine` | Global async engine |
| `async_session_maker` | Session factory |
| `get_db()` | FastAPI dependency for sessions |
| `get_db_context()` | Context manager for sessions |

### `src/core/embeddings.py` — Embeddings

| Symbol | Purpose |
|---|---|
| `EmbeddingService` | Async embedding with API + local fallback |
| `EmbeddingService.embed_text()` | Single text embedding |
| `EmbeddingService.embed_texts()` | Batch text embedding |
| `EmbeddingService._local_embedding()` | BLAKE2b-based deterministic embedding |
| `cosine_similarity()` | Vector similarity calculation |
| `get_embedding_service()` | Cached singleton factory |

### `src/core/vector_db.py` — Vector Databases

| Symbol | Purpose |
|---|---|
| `VectorDBClient` | Abstract base class |
| `ChromaVectorDB` | ChromaDB implementation |
| `PgVectorDB` | PostgreSQL pgvector implementation |
| `get_vector_db()` | Factory function |
| `init_vector_db()` | Initialize and cache |
| `close_vector_db()` | Close connection |
| `get_vector_db_instance()` | Get cached instance |

### `src/core/knowledge_base.py` — Knowledge Base

| Symbol | Purpose |
|---|---|
| `SEED_KNOWLEDGE` | Bundled default knowledge corpus (5 entries) |
| `search_knowledge_entries()` | Primary search function with vector DB + fallback |
| `_format_vector_results()` | Normalize vector DB output |
| `_search_seed_corpus()` | Hybrid semantic + lexical local search |

### `src/core/action_dispatcher.py` — Action Dispatch

| Symbol | Purpose |
|---|---|
| `ActionResult` | Action result model |
| `dispatch_action()` | Main dispatch function (15 action types) |
| `_handle_restart_service()` | Restart via kubectl/systemctl/Docker |
| `_handle_scale()` | Kubernetes scale |
| `_handle_rollback()` | Kubernetes rollout undo |
| `_handle_clear_cache()` | Redis cache clear |
| `_handle_flush_queue()` | Redis queue flush |
| `_handle_failover()` | Failover initiation (simulated) |
| `_handle_block_ip()` | iptables IP blocking |
| `_handle_isolate_host()` | Network isolation |
| `_handle_run_diagnostic()` | Remote diagnostic commands |
| `_handle_collect_logs()` | Log collection |
| `_handle_create_ticket()` | Ticket creation (simulated) |
| `_handle_notify_oncall()` | Notification dispatch |
| `_handle_escalate()` | Escalation |
| `_handle_custom_script()` | Custom script execution |
| `_run_command()` | Async subprocess execution |

### `src/core/approval.py` — Approvals

| Symbol | Purpose |
|---|---|
| `ApprovalStatus` | PENDING, APPROVED, REJECTED, TIMED_OUT |
| `ApprovalRequest` | Approval request with lifecycle methods |
| `create_approval_request()` | Factory with auto-approve in dev |
| `get_approval_request()` | Lookup by ID |
| `list_pending_approvals()` | List with auto-expiry |
| `approve_request()` | Approve + log |
| `reject_request()` | Reject + log |
| `requires_approval()` | Risk-based approval check |

### `src/core/monitoring.py` — Monitoring

| Symbol | Purpose |
|---|---|
| `check_http_health()` | HTTP health check |
| `check_tcp_health()` | TCP port check |
| `query_prometheus()` | PromQL query |
| `query_metrics_for_resource()` | CPU + memory metrics |
| `get_active_alerts_for_resources()` | Alertmanager alerts |
| `analyze_logs_simple()` | Pattern-based log analysis |
| `get_deployment_status_k8s()` | Kubernetes rollout status |
| `correlate_events_across_systems()` | Multi-source event correlation |

### `src/core/validation.py` — Validation

| Symbol | Purpose |
|---|---|
| `run_synthetic_test()` | HTTP health synthetic test |
| `verify_alert_resolution()` | Alert status check |
| `check_incident_compliance()` | Process compliance rules |
| `compare_resource_baselines()` | Metric deviation detection |
| `validate_rollback_completion()` | Rollback health verification |

### `src/core/similar_incidents.py` — Similarity

| Symbol | Purpose |
|---|---|
| `_incident_to_searchable()` | Build searchable text from incident |
| `index_incident()` | Index in vector DB |
| `find_similar()` | Vector search with brute-force fallback |
| `_format_vector_results()` | Normalize vector results |
| `_brute_force_search()` | In-memory cosine similarity |

### `src/core/logging.py` — Logging

| Symbol | Purpose |
|---|---|
| `_CompatLogger` | structlog-compatible adapter for stdlib |
| `configure_logging()` | Setup structlog or stdlib |
| `get_logger()` | Get logger instance |

### `src/core/utils.py` — Utilities

| Symbol | Purpose |
|---|---|
| `enum_val()` | Safe enum-to-string conversion |
| `safe_float()` | Safe float conversion |

---

## Agent Modules

### `src/agents/base.py` — Base Agent

| Symbol | Purpose |
|---|---|
| `BaseAgentState` | Shared agent state model |
| `BaseAgent` | Abstract agent with graph lifecycle |
| `ReactAgent` | ReAct pattern implementation |
| `get_agent()` | Agent factory |

### `src/agents/orchestrator.py`

| Symbol | Purpose |
|---|---|
| `OrchestratorDecision` | Decision model |
| `OrchestratorState` | Extended state |
| `OrchestratorAgent` | Coordination agent |
| `_make_decision()` | LLM decision making |
| `_fallback_decision()` | Rule-based fallback |
| `_execute_decision()` | Decision execution |

### `src/agents/planner.py`

| Symbol | Purpose |
|---|---|
| `RemediationStep` | Individual plan step |
| `RemediationPlan` | Complete plan |
| `PlannerState` | Extended state |
| `PlannerAgent` | Plan creation agent |
| `_create_plan()` | LLM structured output |
| `search_knowledge_base` | Tool |
| `find_similar_incidents` | Tool |

### `src/agents/executor.py`

| Symbol | Purpose |
|---|---|
| `ExecutionResult` | Step result |
| `PlanExecution` | Execution tracker |
| `ExecutorState` | Extended state |
| `ExecutorAgent` | Action execution agent |
| `_execute_step()` | Single step execution |
| `execute_action` | Tool |
| `request_approval` | Tool |
| `initiate_rollback` | Tool |

### `src/agents/observer.py`

| Symbol | Purpose |
|---|---|
| `ObservationResult` | Check result |
| `IncidentObservation` | Full observation report |
| `ObserverState` | Extended state |
| `ObserverAgent` | Monitoring agent |

### `src/agents/validator.py`

| Symbol | Purpose |
|---|---|
| `ValidationResult` | Check result |
| `ValidationReport` | Full validation report |
| `ValidatorState` | Extended state |
| `ValidatorAgent` | Validation agent |
