# Aegis — "Multi-Agent AI Incident Response Platform"
## AI Decision Engine

## Purpose

Document how the platform uses LLMs for decision-making, the integration with LangChain/LangGraph, and the fallback strategies when AI is unavailable.

## Source Traceability

| Component | File |
|---|---|
| LLM provider configuration | `src/core/config.py:LLMSettings` |
| LLM creation | `src/agents/base.py:_create_llm()` |
| LLM invocation | `src/agents/base.py:_call_llm()` |
| Orchestrator LLM decision | `src/agents/orchestrator.py:_make_decision()` |
| Planner structured output | `src/agents/planner.py:_create_plan()` |
| Fallback decision logic | `src/agents/orchestrator.py:_fallback_decision()` |
| ChatOpenAI integration | `src/agents/base.py:119-129` |
| LLM error handling | `src/core/exceptions.py:LLMError` |

## LLM Provider

The platform uses a configurable LLM provider via `pydantic-settings`:

```python
class LLMSettings(BaseSettings):
    provider: str = "openrouter"  # openrouter, openai, anthropic, ollama
    base_url: str = "https://openrouter.ai/api/v1"
    api_key: str = ""
    model: str = "nvidia/nemotron-3-ultra-550b-a55b:free"
    temperature: float = 0.1
    max_tokens: int = 4096
    timeout: int = 120
    max_retries: int = 3
```

From `src/core/config.py:85-103`.

## LLM Integration Points

### 1. Orchestrator Decision Making (`orchestrator.py:173-192`)

The orchestrator sends an incident context summary to the LLM and expects a structured JSON response conforming to `OrchestratorDecision`:

```
System Prompt → [Agent type, responsibilities, decision framework]
Human Message → [Incident details, workflow state, previous decisions]
LLM Response → [JSON decision with action, reason, next_agent, confidence]
```

**Fallback:** If the LLM returns invalid JSON or raises an exception, `_fallback_decision()` provides hardcoded if/else logic based on incident severity and status.

### 2. Planner Remediation Plan (`planner.py:146-165`)

The planner uses `ChatOpenAI.with_structured_output(RemediationPlan)` to get a typed, validated plan directly from the LLM:

```
Context → System Prompt + incident details + KB matches + similar incidents
Output → RemediationPlan with steps, risk assessment, approval requirements
```

**No fallback:** If the LLM fails, the planner returns an error state.

### 3. Agent System Prompts

Each agent has a purpose-built system prompt:

| Agent | Prompt Purpose | Lines |
|---|---|---|
| Orchestrator | Decision framework, severity routing, agent coordination | `orchestrator.py:78-114` |
| Planner | Remediation planning, tool usage, output format | `planner.py:67-92` |
| Executor | Safe execution, approval workflow, rollback procedures | `executor.py:65-96` |
| Observer | Continuous monitoring, alert tracking, anomaly detection | `observer.py:73-94` |
| Validator | Verification checks, compliance, regression detection | `validator.py:79-101` |

## Decision Architecture

### Orchestrator Decision Flow

```
1. Receive incident (new or existing)
2. Build decision context (incident state, completed agents, previous decisions)
3. Call LLM with context + system prompt
4. Parse JSON response
5. If parsing fails → use fallback rules
6. Execute decision (create subtask, update incident, escalate, or close)
7. Check if workflow complete → signal should_continue
```

### Confidence Scoring

The fallback decision engine assigns confidence based on determinism:

| Scenario | Confidence |
|---|---|
| SEV1/SEV2 OPEN incident → plan | 0.9 |
| New incident → plan | 0.8 |
| Plan ready → execute | 0.8 |
| Resolved + validated → close | 0.9 |
| Monitoring | 0.7 |
| No incident context | 0.7 |

## Error Handling

When the LLM is unreachable or returns invalid data:

1. **Invalid JSON:** Caught in `_make_decision()` — logged as warning, triggers fallback
2. **API failure:** Caught in `_call_llm()` — logged, fallback runs
3. **Timeout:** Caught via asyncio — logged, fallback runs
4. **No API key:** LLM constructor succeeds but API call fails — fallback handles

Exception classes for AI failures are defined in `src/core/exceptions.py`:
- `LLMError` — general LLM provider error
- `AgentError` — agent execution error
- `OrchestrationError` — multi-agent orchestration error

## Embedding Service

The `EmbeddingService` (`src/core/embeddings.py`) uses:
1. **Primary:** OpenAI-compatible API via `AsyncOpenAI` (configured via `LLM` settings)
2. **Fallback:** Deterministic local embedding using BLAKE2b hashing + bag-of-tokens TF normalization

The local fallback produces stable, reproducible vectors for offline development and testing, but should not be used in production.

## Current Limitations

- **No streaming** — All LLM calls are synchronous request-response
- **No tool choice** — LangChain `bind_tools` is used but tool selection is entirely LLM-driven
- **No conversation memory** beyond the current task iteration
- **No model fallback chain** — If the primary model fails, no secondary model is tried
- **Structured output only for Planner** — Other agents parse free-text JSON from LLM responses
