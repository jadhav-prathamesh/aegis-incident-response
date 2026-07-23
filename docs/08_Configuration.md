# Aegis — "Multi-Agent AI Incident Response Platform"
## Configuration

## Purpose

Complete reference for all configuration options, environment variables, and settings classes.

## Source Traceability

| Settings Class | File | Env Prefix |
|---|---|---|
| `Settings` | `src/core/config.py:342` | (root, no prefix) |
| `DatabaseSettings` | `src/core/config.py:10` | `DB_` |
| `RedisSettings` | `src/core/config.py:38` | `REDIS_` |
| `VectorDBSettings` | `src/core/config.py:65` | `VECTOR_DB_` |
| `LLMSettings` | `src/core/config.py:85` | `LLM_` |
| `AgentSettings` | `src/core/config.py:105` | `AGENT_` |
| `SecuritySettings` | `src/core/config.py:140` | `SECURITY_` |
| `MonitoringSettings` | `src/core/config.py:169` | `MONITORING_` |
| `IntegrationSettings` | `src/core/config.py:202` | `INTEGRATION_` |
| `KubernetesSettings` | `src/core/config.py:265` | `K8S_` |
| `StorageSettings` | `src/core/config.py:299` | `STORAGE_` |
| `FeatureFlagsSettings` | `src/core/config.py:323` | `FEATURE_` |

## Application Settings (`Settings`)

Root settings that compose all sub-configurations.

| Variable | Default | Description |
|---|---|---|
| `APP_NAME` | "Aegis" | Application display name |
| `APP_VERSION` | "1.0.0" | Application version |
| `APP_ENV` | "development" | Environment (development, staging, production) |
| `DEBUG` | false | Debug mode |
| `LOG_LEVEL` | "INFO" | Logging level |
| `LOG_FORMAT` | "json" | Log format (json, console) |
| `API_PREFIX` | "/api/v1" | API base path |
| `API_HOST` | "0.0.0.0" | Server bind address |
| `API_PORT` | 8000 | Server port |
| `API_WORKERS` | 4 | Uvicorn worker count |

## Database Settings (`DatabaseSettings`)

Prefix: `DB_`

| Variable | Default | Description |
|---|---|---|
| `DB_HOST` | localhost | PostgreSQL host |
| `DB_PORT` | 5432 | PostgreSQL port |
| `DB_USERNAME` | postgres | Database user |
| `DB_PASSWORD` | postgres | Database password |
| `DB_DATABASE` | agentic_platform | Database name |
| `DB_POOL_SIZE` | 20 | Connection pool size |
| `DB_MAX_OVERFLOW` | 10 | Max overflow connections |
| `DB_POOL_TIMEOUT` | 30 | Pool timeout seconds |
| `DB_POOL_RECYCLE` | 3600 | Connection recycle seconds |
| `DB_ECHO` | false | SQL echo logging |
| `DB_SSL_MODE` | prefer | SSL mode for connection |

Properties: `url` (async), `sync_url` (sync).

## Redis Settings (`RedisSettings`)

Prefix: `REDIS_`

| Variable | Default | Description |
|---|---|---|
| `REDIS_HOST` | localhost | Redis host |
| `REDIS_PORT` | 6379 | Redis port |
| `REDIS_USERNAME` | None | Redis username |
| `REDIS_PASSWORD` | None | Redis password |
| `REDIS_DATABASE` | 0 | Redis DB index |
| `REDIS_MAX_CONNECTIONS` | 50 | Max pool connections |
| `REDIS_SOCKET_TIMEOUT` | 5 | Socket timeout |
| `REDIS_SOCKET_CONNECT_TIMEOUT` | 5 | Connect timeout |
| `REDIS_DECODE_RESPONSES` | true | Auto-decode responses |
| `REDIS_DEFAULT_TTL` | 3600 | Default TTL seconds |

Property: `url`.

## Vector DB Settings (`VectorDBSettings`)

Prefix: `VECTOR_DB_`

| Variable | Default | Description |
|---|---|---|
| `VECTOR_DB_PROVIDER` | pgvector | Provider (chroma, pgvector) |
| `VECTOR_DB_EMBEDDING_DIMENSION` | 4096 | Embedding vector size |
| `VECTOR_DB_EMBEDDING_MODEL` | text-embedding-3-small | Embedding model name |
| `VECTOR_DB_COLLECTION_NAME` | knowledge_base | Default collection name |
| `VECTOR_DB_CHROMA_HOST` | localhost | ChromaDB host |
| `VECTOR_DB_CHROMA_PORT` | 8000 | ChromaDB port |
| `VECTOR_DB_CHROMA_AUTH_TOKEN` | None | ChromaDB auth token |
| `VECTOR_DB_CHROMA_SSL` | false | ChromaDB SSL |
| `VECTOR_DB_PGVECTOR_TABLE_PREFIX` | vec_ | pgvector table prefix |

## LLM Settings (`LLMSettings`)

Prefix: `LLM_`

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | openrouter | Provider (openrouter, openai, anthropic, ollama) |
| `LLM_BASE_URL` | https://openrouter.ai/api/v1 | API base URL |
| `LLM_API_KEY` | "" | API key |
| `LLM_MODEL` | nvidia/nemotron-3-ultra-550b-a55b:free | Model name |
| `LLM_TEMPERATURE` | 0.1 | Temperature (0.0-2.0) |
| `LLM_MAX_TOKENS` | 4096 | Max tokens per response |
| `LLM_TIMEOUT` | 120 | Request timeout |
| `LLM_MAX_RETRIES` | 3 | Max retry attempts |
| `LLM_RETRY_DELAY` | 1.0 | Delay between retries |
| `LLM_OPENROUTER_SITE_URL` | https://app.example.com | OpenRouter site URL |
| `LLM_OPENROUTER_APP_NAME` | Aegis | OpenRouter app name |

## Agent Settings (`AgentSettings`)

Prefix: `AGENT_`

Each agent type has a configurable model name (e.g., `AGENT_ORCHESTRATOR_MODEL`, `AGENT_PLANNER_MODEL`, etc.), all defaulting to the free Nemotron model.

Shared settings:
| Variable | Default | Description |
|---|---|---|
| `AGENT_DEFAULT_TEMPERATURE` | 0.1 | Default LLM temperature |
| `AGENT_DEFAULT_MAX_TOKENS` | 4096 | Default max tokens |
| `AGENT_DEFAULT_TIMEOUT` | 300 | Default timeout seconds |
| `AGENT_MAX_RETRIES` | 3 | Max retry count |
| `AGENT_RETRY_DELAY` | 5.0 | Retry delay seconds |
| `AGENT_MEMORY_ENABLED` | true | Enable agent memory |
| `AGENT_MEMORY_WINDOW` | 10 | Memory context window |
| `AGENT_ENABLE_SHELL_TOOLS` | true | Shell command tools |
| `AGENT_ENABLE_K8S_TOOLS` | true | Kubernetes tools |
| `AGENT_ENABLE_CLOUD_TOOLS` | true | Cloud provider tools |
| `AGENT_ENABLE_SERVICENOW_TOOLS` | true | ServiceNow tools |
| `AGENT_ENABLE_MONITORING_TOOLS` | true | Monitoring tools |

## Security Settings (`SecuritySettings`)

Prefix: `SECURITY_`

| Variable | Default | Description |
|---|---|---|
| `SECURITY_SECRET_KEY` | "change-me-in-production" | JWT signing key |
| `SECURITY_ALGORITHM` | HS256 | JWT algorithm |
| `SECURITY_ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | Access token TTL |
| `SECURITY_REFRESH_TOKEN_EXPIRE_DAYS` | 7 | Refresh token TTL |
| `SECURITY_API_KEY_HEADER` | X-API-Key | API key header name |
| `SECURITY_RATE_LIMIT_REQUESTS` | 100 | Rate limit count |
| `SECURITY_RATE_LIMIT_WINDOW_SECONDS` | 60 | Rate limit window |
| `SECURITY_CORS_ORIGINS` | ["http://localhost:3000", "http://localhost:8080"] | Allowed CORS origins |
| `SECURITY_ENCRYPTION_KEY` | None | Encryption key |
| `SECURITY_AUDIT_ENABLED` | true | Audit logging |

## Feature Flags (`FeatureFlagsSettings`)

Prefix: `FEATURE_`

| Variable | Default | Description |
|---|---|---|
| `FEATURE_ENABLE_SELF_HEALING` | true | Self-healing remediation |
| `FEATURE_ENABLE_PREDICTIVE_FAILURE` | true | Predictive failure detection |
| `FEATURE_ENABLE_RCA_ANALYSIS` | true | Root cause analysis |
| `FEATURE_ENABLE_INTELLIGENT_ROUTING` | true | Intelligent ticket routing |
| `FEATURE_ENABLE_INCIDENT_PRIORITIZATION` | true | Incident prioritization |
| `FEATURE_ENABLE_KNOWLEDGE_BASE` | true | Knowledge base search |
| `FEATURE_ENABLE_MULTI_AGENT_ORCHESTRATION` | true | Multi-agent coordination |
| `FEATURE_ENABLE_HUMAN_IN_LOOP` | true | Human approval workflows |
| `FEATURE_ENABLE_AUDIT_LOGGING` | true | Audit trail |
| `FEATURE_ENABLE_COST_OPTIMIZATION` | false | Cost optimization |
| `FEATURE_ENABLE_CHAOS_ENGINEERING` | false | Chaos engineering |
| `FEATURE_ENABLE_GITOPS` | false | GitOps deployment |

## Environment File

Copy `.env.example` to `.env` and customize. The `.env` file is loaded automatically by `pydantic-settings`.
