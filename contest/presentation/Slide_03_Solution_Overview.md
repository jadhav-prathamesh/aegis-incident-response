# Slide 3: Solution Overview

## Content

**Aegis — "Multi-Agent AI Incident Response Platform"**

A multi-agent AI system that automates the entire incident lifecycle.

| Component | Role | Intelligence |
|---|---|---|
| Observer | Detect & Diagnose | Health checks + metrics |
| Orchestrator | Coordinate & Decide | LLM reasoning |
| Planner | Strategize | Knowledge + LLM |
| Executor | Act | 15 action types |
| Validator | Verify | 6 check types |

**Automation Coverage:** ~70% of common L1/L2 incidents

## Design Notes

- Central diagram: 5 boxes arranged in a circle/pentagon
- Arrow flow: Observe → Reason → Plan → Decide → Execute → Validate
- Each box has icon + one-line description
- Bottom summary bar with coverage percentage

## Speaker Notes

"Our platform uses five specialized AI agents working in sequence. The Observer detects issues, the Orchestrator coordinates using an LLM, the Planner designs remediation, the Executor carries it out, and the Validator confirms the fix worked."
