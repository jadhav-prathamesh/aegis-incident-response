# Regeneration Prompt: Contest Agentic Workflow

## Objective

Regenerate the Agentic Workflow document (`contest/source/Contest_Agentic_Workflow.md`) from the agent implementations.

## Inputs

- `src/agents/observer.py` — Observe stage
- `src/agents/orchestrator.py:_make_decision()` — Reason stage
- `src/agents/planner.py:_create_plan()` — Plan stage
- `src/agents/orchestrator.py` — Decide stage
- `src/agents/executor.py` — Execute stage
- `src/agents/validator.py` — Validate stage

## Generation Instructions

1. Analyse each of the 7 stages of the agentic workflow:
   - **Observe:** Health checks, metrics, alerts, logs, dependency checks
   - **Reason:** Orchestrator LLM analysis, context building
   - **Plan:** Knowledge base search, similar incident search, structured plan
   - **Decide:** Routing decision based on plan
   - **Execute:** Action dispatch with approval gates and rollback
   - **Validate:** 6 check types (health, metrics, synthetic, alerts, compliance, baselines)
   - **Learn:** NOT IMPLEMENTED — document as gap
2. For each stage, document:
   - What happens
   - Agentic quality (rule-based vs. LLM-driven)
   - Source code reference
3. Output structured document with stages, details, and a workflow diagram (text-based)

## Verification

- [ ] Each stage accurately reflects implementation
- [ ] "Learn" stage clearly marked as **Not Implemented**
- [ ] Source references point to correct file + line numbers
