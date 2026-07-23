# Aegis — "Multi-Agent AI Incident Response Platform"
## Glossary

## Source Traceability

Terms defined here correspond to code and configuration files in the repository.

---

### A

**Action Dispatcher**
Module (`src/core/action_dispatcher.py`) that routes remediation actions to the appropriate handler. Supports 15 action types.

**Agent**
An AI-powered component in the multi-agent system, built on LangGraph, responsible for a specific function (orchestration, planning, execution, observation, validation).

**Agent Factory**
Function `get_agent()` in `src/agents/base.py` that creates and caches agent instances by `AgentType`.

**AgentResult**
Message object returned by an agent after task execution, containing success status, output, artifacts, and confidence score.

**AgentTask**
Message object sent to an agent containing task type, input data, context, and configuration.

**AgentType**
Enum in `src/core/models.py` listing all agent types. Implemented: ORCHESTRATOR, PLANNER, EXECUTOR, OBSERVER, VALIDATOR.

**ApprovalRequest**
Object in `src/core/approval.py` representing a pending human approval for a high-risk action.

**AsyncPG**
PostgreSQL async driver used by SQLAlchemy in `src/core/database.py`.

---

### B

**BaseAgent**
Abstract base class in `src/agents/base.py` providing LLM initialization, LangGraph lifecycle, and health checks for all agents.

---

### C

**ChromaDB**
Vector database backend implemented in `ChromaVectorDB` (`src/core/vector_db.py:68`).

**ChatOpenAI**
LangChain LLM wrapper used by all agents (`src/agents/base.py:121`). Configured via OpenRouter-compatible API.

**CORS**
Cross-Origin Resource Sharing middleware configured in `src/api/app.py:37`.

---

### D

**Dashboard**
Streamlit application at `src/dashboard/app.py` providing operational overview, incident management, and approval workflow.

---

### E

**EmbeddingService**
Service in `src/core/embeddings.py` that creates vector embeddings via OpenAI-compatible API with local hashing fallback.

**ExecutorAgent**
Agent that executes remediation plan steps with approval gates and rollback support (`src/agents/executor.py`).

---

### F

**Fallback Decision**
Hardcoded if/else logic in `OrchestratorAgent._fallback_decision()` used when the LLM is unavailable (`src/agents/orchestrator.py:222`).

**Feature Flag**
Configuration in `FeatureFlagsSettings` (`src/core/config.py:323`) to enable/disable capabilities without code changes.

---

### I

**Incident**
Core domain model in `src/core/models.py:173` representing a production incident with lifecycle status, severity, category, and resolution data.

**IncidentStore**
In-memory repository for incidents (`src/core/incident_store.py`). Transient — not persisted across restarts.

---

### K

**Knowledge Base**
Module (`src/core/knowledge_base.py`) providing hybrid semantic + lexical search against vector DB with seed corpus fallback.

---

### L

**LangGraph**
Framework used to build agent state machines (`src/agents/base.py`). Provides graph-based execution with state management and checkpointing.

**LLM (Large Language Model)**
Used by agents for decision-making and plan generation. Configured via `LLMSettings` (`src/core/config.py:85`).

---

### M

**MemorySaver**
LangGraph checkpointing mechanism (`src/agents/base.py:155`) that persists agent state between execution steps.

**Multi-Agent System**
Architecture where multiple specialized AI agents coordinate under an orchestrator to handle complex incidents.

---

### O

**ObserverAgent**
Agent that monitors system health during and after remediation (`src/agents/observer.py`).

**OrchestratorAgent**
Central coordination agent that receives incidents, makes decisions, and routes to specialized agents (`src/agents/orchestrator.py`).

**OrchestratorDecision**
Pydantic model representing the orchestrator's decision (action, reason, next_agent, payload, confidence).

---

### P

**pgvector**
PostgreSQL extension for vector similarity search. Implemented in `PgVectorDB` (`src/core/vector_db.py:186`).

**PlannerAgent**
Agent that creates structured remediation plans using LLM and knowledge base (`src/agents/planner.py`).

**Prometheus**
Monitoring system configured in `config/prometheus.yml` for metrics collection and alerting.

---

### R

**ReAct (Reasoning + Acting)**
Pattern implemented in `ReactAgent` (`src/agents/base.py:254`) where the agent alternates between LLM reasoning and tool execution.

**RemediationPlan**
Structured output from the planner containing ordered steps, risk assessment, and approval requirements (`src/agents/planner.py:39`).

---

### S

**Structlog**
Structured logging library configured in `src/core/logging.py`. Falls back to stdlib logging when unavailable.

---

### T

**Tool**
LangChain tool function decorated with `@tool` that an agent can invoke. Each agent has a set of specialized tools.

---

### U

**use_enum_values**
Pydantic model configuration (`src/core/models.py:16`) that stores enum fields as plain strings to simplify serialization.

---

### V

**ValidatorAgent**
Agent that verifies remediation success through health checks, synthetic tests, compliance, and baseline comparison (`src/agents/validator.py`).

**Vector Database**
Database optimized for similarity search. Supported backends: ChromaDB, pgvector (`src/core/vector_db.py`).

---

### W

**Workflow**
The end-to-end incident management flow: create → plan → execute → observe → validate → close.
