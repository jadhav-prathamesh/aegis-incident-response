# Slide 5: Agentic Workflow

## Content

**How It Works: 7-Stage Agentic Loop**

```
┌─────────┐
│ OBSERVE │ ← Health checks, metrics, alerts, logs
└────┬────┘
     ▼
┌─────────┐
│  REASON │ ← LLM analyzes context, decides next action
└────┬────┘
     ▼
┌─────────┐
│  PLAN   │ ← KB search + similar incidents + structured plan
└────┬────┘
     ▼
┌─────────┐
│  DECIDE │ ← Route to executor or escalate to human
└────┬────┘
     ▼
┌─────────┐
│ EXECUTE │ ← 15 action types with approval gates & rollback
└────┬────┘
     ▼
┌─────────┐
│VALIDATE │ ← Health, metrics, synthetic, compliance, baselines
└────┬────┘
     ▼
┌─────────┐
│  LEARN  │ ← NOT IMPLEMENTED (future enhancement)
└─────────┘
```

**LLM Integration:** Structured outputs for typed plans and decisions. Fallback to rule-based engine when LLM unavailable.

## Design Notes

- Vertical flow diagram with arrows between stages
- Stage 7 (Learn) greyed out / dashed border
- Each stage box has 2-3 key action words
- Colour gradient from green (start) to amber (end)

## Speaker Notes

"This is the core innovation — a seven-stage agentic loop. Each stage is handled by a specialized agent. The Orchestrator uses an LLM to reason about the incident and decide the best path forward. If the LLM is unavailable, it falls back to deterministic rules."
