# Contest AI Solution

## Overview

The solution uses a **multi-agent AI orchestration** pattern where 5 specialized LangGraph agents collaborate to handle production incidents autonomously. Each agent has a specific role and uses LLM reasoning augmented with deterministic tools and fallback logic.

## AI Components

### 1. LangGraph State Machines

Every agent uses LangGraph's `StateGraph` for structured execution:

```
Graph Structure:
  START → process → (continue → tools → process) OR (end → END)
```

- State is typed via Pydantic models (e.g., `OrchestratorState`, `PlannerState`)
- Checkpointing via LangGraph `MemorySaver` for state persistence
- Conditional edges based on `_should_continue()` logic

Source: `src/agents/base.py:131-156`

### 2. LLM Integration

Model: `nvidia/nemotron-3-ultra-550b-a55b:free` via OpenRouter (configurable)

| Agent | LLM Usage | Output |
|---|---|---|
| Orchestrator | Decision-making (JSON) | `OrchestratorDecision` |
| Planner | Structured plan generation | `RemediationPlan` (via `with_structured_output`) |
| Executor | No direct LLM (tool-based) | Procedural |
| Observer | Via ReAct pattern | `IncidentObservation` |
| Validator | Via ReAct pattern | `ValidationReport` |

Source: `src/core/config.py:85-103`

### 3. ReAct Pattern

The `ReactAgent` class (`src/agents/base.py:254-335`) implements the Reasoning + Acting pattern:

1. System prompt sets agent role and responsibilities
2. Context message provides incident state
3. Task message provides input
4. LLM response → tool calls or final answer
5. Tool results → next iteration or completion

### 4. Fallback Decision Engine

When the LLM is unavailable, the Orchestrator uses a hardcoded fallback:

```
OPEN + SEV1/SEV2 → plan (confidence 0.9)
OPEN + lower → plan (confidence 0.8)
INVESTIGATING + no planner → plan
INVESTIGATING + planner done → execute
RESOLVING + no validator → validate
RESOLVING + validator done → close
```

Source: `src/agents/orchestrator.py:222-286`

### 5. Embedding Service

The `EmbeddingService` (`src/core/embeddings.py`) provides:
- Primary: OpenAI-compatible API via `AsyncOpenAI`
- Fallback: Deterministic BLAKE2b-based local embeddings

The fallback produces stable vectors for offline development but uses a bag-of-tokens hashing approach, not semantic embeddings.

### 6. Knowledge Base Search

Hybrid search strategy:
```
1. Embed query text
2. Try vector DB search (ChromaDB or pgvector)
3. If vector DB fails: search seed corpus
   - Semantic score (cosine similarity): 70%
   - Lexical score (term matching): 30%
   - Combined score → top_k results
```

Source: `src/core/knowledge_base.py`

### 7. Similar Incident Retrieval

Similarity search for past incidents:
```
1. Build searchable text from incident (title, description, severity, category)
2. Embed via embedding service
3. Vector DB search (exclude self)
4. If fails: brute-force cosine similarity against all in-memory incidents
```

Source: `src/core/similar_incidents.py`

## AI Safety Features

| Feature | Implementation |
|---|---|
| Approval gates | 8 action types require human approval |
| Dry-run mode | Actions can be tested without execution |
| Risk classification | Each plan step has risk level (LOW → CRITICAL) |
| Rollback procedures | Automated rollback on step failure |
| Confidence scoring | Agents report confidence (0.0-1.0) |
| Fallback logic | System operates without LLM (degraded mode) |
| Audit logging | All decisions and actions logged |

## AI Limitations

| Limitation | Impact |
|---|---|
| No streaming LLM | Higher latency for multi-step reasoning |
| No model fallback chain | Single model point of failure |
| No conversation memory | Each task treated independently |
| No learning loop | System does not improve from past outcomes |
| No A/B testing | No mechanism to compare decision strategies |
