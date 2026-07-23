# Regeneration Prompt: Contest Problem Statement

## Objective

Regenerate the Problem Statement (`contest/source/Contest_Problem_Statement.md`) from the codebase and industry context.

## Inputs

- `src/core/models.py` — Incident model, severity, category
- `src/core/action_dispatcher.py` — Action types
- `src/core/knowledge_base.py` — Knowledge management
- Industry context: AIOps market reports (external)

## Generation Instructions

1. Analyse the incident model: what operational problems does it model?
2. Identify which manual toil is automated by the agent pipeline
3. Map each agent to a specific operational problem it solves
4. Quantify the problem space: number of incident states, action types, service checks
5. Describe the operational context (infrastructure monitoring, incident response)
6. Output structured document with sections: Background, Problem Statement, Current Challenges, Why AI Agents, Impact

## Verification

- [ ] Problem maps to actual codebase capabilities
- [ ] Challenges are derived from source code gaps
- [ ] No fabricated industry statistics
