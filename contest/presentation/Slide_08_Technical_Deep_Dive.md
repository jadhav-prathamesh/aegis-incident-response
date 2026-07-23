# Slide 8: Technical Deep Dive

## Content

**Key Technical Decisions**

| Decision | Choice | Rationale |
|---|---|---|
| Agent Framework | LangGraph StateGraph | Native state machine, tool calling |
| LLM Provider | OpenRouter | Multi-model access, fallback options |
| Embedding Model | text-embedding-3-small | 1536-dim, cost-effective |
| Vector DB | ChromaDB + pgvector | Dev convenience + production-grade |
| Knowledge Search | Hybrid (vector + lexical) | Best recall for runbook matching |
| Validation | 6 check types | Comprehensive fix verification |

**Codebase Stats:**
- Python files: 30+ across `src/agents/`, `src/core/`, `src/api/`
- Tests: 93 passing
- API endpoints: 23
- Action types: 15

## Design Notes

- Two-column layout: left (table), right (stats)
- Codebase stats in highlight cards
- Architecture decision labels: (Implemented / Plan)
- Minimal text, maximum data

## Speaker Notes

"Some key technical decisions: we chose LangGraph for its native state machine support, OpenRouter for flexible LLM access, and dual vector DB support for both development and production. The codebase includes 93 tests and 23 API endpoints."
