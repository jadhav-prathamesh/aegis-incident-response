# Aegis — "Multi-Agent AI Incident Response Platform"
## Frequently Asked Questions

## Source Traceability

Answers are derived from the actual implementation.

---

### General

**Q: What is Aegis?**
A: An open-source autonomous AI operations engineer that automates production incident management using a multi-agent LangGraph architecture. It handles the full incident lifecycle: ingestion, RCA, remediation planning, execution, monitoring, and validation.

**Q: Is this production-ready?**
A: Partially. The architecture and codebase are designed for production, but several components are not production-hardened: no authentication, in-memory incident store, stubbed cloud integrations, no CI/CD pipeline. See `docs/16_Security.md` and `docs/09_Deployment_Guide.md` for details.

**Q: Does this require an LLM API key?**
A: Yes, for full functionality. The default configuration uses OpenRouter's free Nemotron model. Without an API key, the fallback decision engine operates but LLM-based planning and decision-making will not work.

---

### Architecture

**Q: What is the difference between the Orchestrator and the other agents?**
A: The Orchestrator is the decision-maker. It receives incidents, decides what should happen next (plan, execute, observe, validate, close), and routes tasks to the appropriate specialized agent. It does not execute actions itself.

**Q: Can agents run in parallel?**
A: Currently, agents run sequentially. The Orchestrator routes to one agent at a time. Parallel execution is a future enhancement.

**Q: How do agents communicate?**
A: Through `AgentTask` and `AgentResult` message objects. The Orchestrator creates tasks and stores them in shared state. There is no message bus — communication is orchestration-mediated.

---

### Data Storage

**Q: Where are incidents stored?**
A: In an in-memory dictionary (`src/core/incident_store.py`). PostgreSQL is configured in `src/core/database.py` but the incident store does not use it yet.

**Q: Is data persisted across restarts?**
A: No. The in-memory incident store loses all data on restart. Docker volumes persist database data if PostgreSQL is running.

**Q: What vector database should I use?**
A: Either ChromaDB or pgvector. The default is pgvector. Both are configured and the system provides an abstract client interface.

---

### AI & LLM

**Q: Which LLM providers are supported?**
A: OpenRouter (default), OpenAI, Anthropic, and Ollama. Configured via `LLM_PROVIDER` and related env vars.

**Q: What happens if the LLM is unavailable?**
A: The Orchestrator falls back to hardcoded if/else decision rules. The embedding service falls back to a deterministic local embedding. Core functionality degrades but does not crash.

**Q: Are LLM calls tested?**
A: No end-to-end LLM tests exist. All tests mock LLM calls. This is a known gap.

---

### Testing

**Q: How many tests are there?**
A: 93 tests: 8 action dispatcher, 26 orchestrator, 28 pipeline, 8 API, 6 approval, 6 dashboard, 3 planner search, 3 similar incidents.

**Q: Are there integration tests?**
A: The API tests use FastAPI TestClient but mock all external dependencies. There are no true integration tests connecting to real databases or LLMs.

**Q: How do I run tests?**
A: `python -m pytest tests/ -v`

---

### Deployment

**Q: How do I deploy?**
A: `docker-compose up -d` starts all services. See `docs/09_Deployment_Guide.md` for details.

**Q: What ports are used?**
A: API (8000), Dashboard (8501), PostgreSQL (5432), Redis (6379), ChromaDB (8100), Prometheus (9090), Grafana (3000).

**Q: Is Kubernetes supported?**
A: Kubernetes settings exist in `KubernetesSettings` but no manifests are provided. The `kubernetes_action` tool is a stub.

---

### Security

**Q: Is authentication implemented?**
A: No. JWT settings exist but no middleware is wired. The API is publicly accessible.

**Q: Is the API encrypted?**
A: No. There is no HTTPS/TLS configuration. Production deployment requires a reverse proxy.

---

### Monitoring

**Q: What monitoring is built in?**
A: Health checks (HTTP/TCP), Prometheus metrics queries, Alertmanager integration, log analysis, and event correlation.

**Q: Is there a metrics endpoint?**
A: Prometheus is configured to scrape `/metrics` but the FastAPI application does not expose this endpoint. This requires additional instrumentation.

---

### Business

**Q: Is this free?**
A: Yes, MIT-licensed open source.

**Q: Can I use this in production?**
A: Yes, with the caveats listed above. The gaps requiring attention are documented in `docs/16_Security.md` and `docs/09_Deployment_Guide.md`.

**Q: Who maintains this?**
A: This is an open-source project. See `README.md` for contribution guidelines.
