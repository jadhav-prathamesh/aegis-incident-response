# Slide 4: System Architecture

## Content

**Architecture Overview**

- **Backend:** Python 3.12, FastAPI, LangGraph
- **AI:** Multi-agent LLM orchestration (OpenRouter, Qwen 2.5)
- **Storage:** PostgreSQL + pgvector, ChromaDB (dual vector DB)
- **Monitoring:** Prometheus + Grafana
- **UI:** Streamlit dashboard
- **Deployment:** Docker Compose (7 services)

**Language & Framework Choices:**
- Python for AI/ML ecosystem
- LangGraph for agent state machines
- FastAPI for async performance
- pgvector for production vector search

## Design Notes

- Architecture layers diagram (top to bottom):
  - UI Layer (Streamlit)
  - API Layer (FastAPI)
  - Agent Layer (LangGraph)
  - AI Layer (LLM + Embeddings)
  - Data Layer (PostgreSQL, ChromaDB, Redis)
- Each layer labelled with technology

## Speaker Notes

"The platform is built with a clean layered architecture. Python and LangGraph power the AI agent layer, FastAPI serves the API, and we use PostgreSQL with pgvector for both relational data and vector embeddings. Everything runs in Docker Compose."
