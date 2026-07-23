# Regeneration Prompt: Contest Solution Architecture

## Objective

Regenerate the Solution Architecture document (`contest/source/Contest_Solution_Architecture.md`) from the codebase.

## Inputs

- `docs/02_System_Architecture.md` — System architecture
- `docs/03_Agent_Architecture.md` — Agent architecture
- `docs/04_Agent_Interaction.md` — Agent interaction patterns
- `src/agents/` — All agent implementations
- `src/core/` — All core services
- `docker-compose.yml` — Service topology
- `src/core/config.py` — Service configuration

## Generation Instructions

1. Document the system architecture from docker-compose:
   - API service
   - Dashboard (Streamlit)
   - PostgreSQL + pgvector
   - Redis
   - ChromaDB
   - Prometheus
   - Grafana
2. Document the agent architecture from `src/agents/`:
   - Base agent class with StateGraph
   - 5 agent types (Orchestrator, Observer, Planner, Executor, Validator)
   - Agent interaction flow (Observe → Reason → Plan → Decide → Execute → Validate → Learn)
3. Document data flow:
   - Incident creation → agent pipeline → resolution
   - Knowledge base search during planning
   - Vector similarity for incident matching
4. Output structured document with sections: System Architecture, Agent Architecture, Data Flow, Service Topology, Deployment Architecture

## Verification

- [ ] Architecture matches docker-compose.yml exactly
- [ ] Agent types match implemented classes
- [ ] Data flow matches agent pipeline logic
- [ ] No fabricated components
