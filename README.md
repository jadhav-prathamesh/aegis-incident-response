<div align="center">
  <h1>Aegis 🛡️</h1>
  <p><strong>Multi-Agent AI Incident Response Platform</strong></p>
  <p><em>Stop chasing production fires. Let AI handle the runbook.</em></p>

  <p>
    <a href="#-why-aegis"><strong>Why Aegis?</strong></a> •
    <a href="#-architecture"><strong>Architecture</strong></a> •
    <a href="#-quick-start"><strong>Quick Start</strong></a> •
    <a href="#-api-overview"><strong>API</strong></a> •
    <a href="#-contributing"><strong>Contributing</strong></a>
  </p>

  <p>
    <img src="https://img.shields.io/badge/python-3.12%2B-blue" alt="Python 3.12+">
    <img src="https://img.shields.io/badge/license-Apache%202.0-green" alt="Apache 2.0">
    <img src="https://img.shields.io/badge/tests-54%20passing-brightgreen" alt="54 tests passing">
    <img src="https://img.shields.io/badge/agents-5-blueviolet" alt="5 agents">
    <img src="https://img.shields.io/badge/PRs-welcome-orange" alt="PRs welcome">
  </p>
</div>

---

## 💭 Why Aegis?

**You're on-call at 2 AM.** PagerDuty screams — production is down. You scramble to understand the error, dig through logs, search runbooks, apply a fix, monitor recovery, and verify everything's clean. By the time you're done, it's 4 AM and you've got a post-mortem to write.

**What if instead, you could just say "fix it"?**

That's Aegis. It's an AI-powered platform that automates the entire incident response lifecycle — from detection to remediation to validation. Think of it as your tireless SRE sidekick who never sleeps, never gets tired, and knows every runbook by heart.

### Who is this for?

| Role | What Aegis does for you |
|------|------------------------|
| 🧑‍💻 **SRE / DevOps Engineer** | Automates runbook execution, reduces MTTR, eliminates toil |
| 👨‍💼 **Engineering Manager** | Tracks incident trends, measures team response effectiveness |
| 🏢 **Platform Team** | Embeddable API, extensible agent framework, custom actions |
| 🎓 **Cloud Enthusiast** | Learn multi-agent AI architectures, LangGraph, vector search in practice |

### The Problem

- **Incident response is reactive.** You find out about issues when users complain, not when they start.
- **Runbooks are manual.** Even with documentation, every incident requires humans to read, interpret, and execute steps.
- **Knowledge is siloed.** Only senior engineers know how to fix certain issues — and they're the ones getting paged at 3 AM.
- **Post-mortems are late.** By the time you analyze what happened, the context is cold.

### The Aegis Solution

1. **🤖 Autonomous agents** that understand incidents, plan fixes, execute actions, monitor results, and validate success
2. **🧠 LLM-powered reasoning** using LangGraph for structured, auditable decision-making
3. **📚 Vector search** across past incidents to find similar issues and solutions instantly
4. **🔌 API-first design** — integrate with PagerDuty, Slack, Jira, or your own tools
5. **✅ Built-in validation** — synthetic tests, compliance checks, baseline comparisons

---

## 🏗️ Architecture

```
                   ┌─────────────────────────────────────────────────┐
                   │                   Incident                      │
                   └──────────┬──────────────────────────────────────┘
                              │
                   ┌──────────▼──────────┐
                   │    Orchestrator     │  ◀── LLM decides what to do
                   │  (Decision Engine)  │
                   └──────────┬──────────┘
                              │
              ┌───────────────┼───────────────────┐
              │               │                    │
    ┌─────────▼───────┐  ┌───▼────────┐  ┌───────▼────────┐
    │    Planner      │  │  Executor  │  │    Observer    │
    │  (RCA + Search) │  │ (Actions)  │  │ (Health +      │
    │                 │  │            │  │  Metrics)      │
    └─────────┬───────┘  └───┬────────┘  └───────┬────────┘
              │              │                    │
              └──────────────┼────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   Validator     │  ◀── Did the fix work?
                    │  (Tests +       │
                    │   Compliance)   │
                    └─────────────────┘
```

### The 5 Agents

| Agent | 🎯 Role | What it does |
|-------|---------|--------------|
| **🔄 Orchestrator** | The Brain | Receives incidents, uses LLM to understand severity & type, decides which agents to activate, coordinates the full response |
| **📋 Planner** | The Strategist | Breaks down incidents into actionable tasks, searches vector DB for similar past incidents, creates a remediation plan |
| **⚡ Executor** | The Doer | Runs approved actions — restart services, scale deployments, rollback versions, failover regions, clear caches |
| **👁️ Observer** | The Watcher | Monitors recovery via health checks, Prometheus metrics, log analysis, alert correlation |
| **✅ Validator** | The Inspector | Verifies fixes with synthetic tests, compliance checks, baseline comparisons — ensures the problem is really gone |

### Tech Stack

| Layer | Technology |
|-------|-----------|
| 🐍 **Language** | Python 3.12+ |
| 🧠 **AI Framework** | LangGraph, LangChain, OpenAI-compatible APIs |
| 🌐 **Backend** | FastAPI + uvicorn |
| 🔍 **Vector DB** | ChromaDB / pgvector |
| 💾 **Cache** | Redis |
| 🗄️ **Database** | PostgreSQL (asyncpg) |
| 📊 **Monitoring** | Prometheus, Grafana |
| 📈 **Dashboard** | Streamlit |
| 🐳 **Infrastructure** | Docker, Docker Compose |
| ✅ **Testing** | pytest (54 tests) |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+** — [Download](https://www.python.org/downloads/)
- **Docker & Docker Compose** — for full stack (optional)

### 🪟 Local Development (Windows / Mac / Linux)

```bash
# 1. Clone the repo
git clone https://github.com/jadhav-prathamesh/aegis-incident-response.git
cd aegis-incident-response

# 2. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate     # Linux/Mac
# .venv\Scripts\activate       # Windows

# 3. Install all dependencies
pip install -e ".[dev]"

# 4. Run all 54 tests
python -m pytest tests/ -v

# 5. Start the API server
python -m src.main
```

> 🎉 **Your API is now running at** [http://localhost:8000](http://localhost:8000)

### 🐳 Docker Compose (Full Stack)

```bash
# Copy the example config
cp .env.example .env

# Start everything — API, Dashboard, DB, Redis, Prometheus, Grafana
docker-compose up -d
```

| Service | Address | What it is |
|---------|---------|------------|
| 🚪 **API** | http://localhost:8000 | FastAPI REST backend |
| 📊 **Dashboard** | http://localhost:8501 | Streamlit UI |
| 🗄️ **PostgreSQL** | localhost:5432 | Primary database |
| ⚡ **Redis** | localhost:6379 | Cache & queue |
| 🔍 **ChromaDB** | localhost:8100 | Vector embeddings |
| 📈 **Prometheus** | localhost:9090 | Metrics collection |
| 📉 **Grafana** | localhost:3000 | Metrics visualization |

### 🔥 Quick API Test

```bash
# Check if the API is alive
curl http://localhost:8000/health

# Response:
# {"status":"healthy","version":"1.0.0"}
```

---

## 📡 API Overview

### Health & Readiness

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Liveness probe — is the server alive? |
| `GET` | `/ready` | Readiness probe — is the server ready to accept traffic? |
| `GET` | `/info` | Platform info (version, config status) |

### Incidents 🚨

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/incidents` | List all incidents |
| `GET` | `/api/v1/incidents/{id}` | Get incident details |
| `POST` | `/api/v1/incidents` | Create a new incident |
| `PATCH` | `/api/v1/incidents/{id}` | Update incident status |
| `GET` | `/api/v1/incidents/{id}/similar` | Find similar past incidents |

### Approvals ✅

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/approvals/pending` | List pending approval requests |
| `POST` | `/api/v1/approvals` | Create an approval request |
| `POST` | `/api/v1/approvals/{id}/approve` | Approve an action |
| `POST` | `/api/v1/approvals/{id}/reject` | Reject an action |

### Agents 🤖

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/agents/execute` | Execute an agent task |
| `GET` | `/api/v1/agents/types` | List available agent types |
| `GET` | `/api/v1/agents/{type}/health` | Check an agent's health |

### Monitoring 🔍

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/monitoring/health/{service}` | HTTP health check for a service |
| `GET` | `/api/v1/monitoring/metrics/{resource}` | Resource metrics (CPU, mem, etc.) |
| `GET` | `/api/v1/monitoring/alerts` | Active alerts |
| `GET` | `/api/v1/monitoring/deployments/{service}` | Deployment status |

### Validation ✅

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/validation/synthetic` | Run a synthetic test |
| `POST` | `/api/v1/validation/alerts` | Verify alert resolution |
| `POST` | `/api/v1/validation/compliance` | Check compliance against policies |
| `POST` | `/api/v1/validation/baselines` | Compare against performance baselines |
| `POST` | `/api/v1/validation/rollback` | Validate a rollback is safe |

---

## 📁 Project Structure

```
aegis-incident-response/
│
├── src/
│   ├── core/               # Core domain logic, models, services
│   │   ├── models.py       # 30+ Pydantic domain models & enums
│   │   ├── config.py       # 11 nested config groups (pydantic-settings)
│   │   ├── exceptions.py   # 30+ typed exceptions with HTTP mapping
│   │   ├── vector_db.py    # ChromaDB & pgvector backends
│   │   ├── embeddings.py   # OpenAI embeddings with local fallback
│   │   ├── knowledge_base.py  # Semantic + lexical hybrid search
│   │   ├── action_dispatcher.py # 15 action handlers
│   │   ├── approval.py     # Full approval workflow
│   │   ├── monitoring.py   # Health, Prometheus, Alertmanager
│   │   ├── validation.py   # Synthetic tests, compliance, baselines
│   │   ├── incident_store.py  # In-memory incident repo
│   │   ├── similar_incidents.py # Vector + brute-force similarity
│   │   ├── utils.py        # Shared utilities
│   │   ├── logging.py      # Structlog with stdlib fallback
│   │   └── database.py     # Async PostgreSQL (asyncpg)
│   │
│   ├── agents/             # LangGraph agent implementations
│   │   ├── base.py         # Abstract base agent
│   │   ├── orchestrator.py # Decision engine
│   │   ├── planner.py      # RCA & remediation planning
│   │   ├── executor.py     # Action execution
│   │   ├── observer.py     # Monitoring & health checks
│   │   └── validator.py    # Fix verification
│   │
│   ├── api/                # FastAPI REST endpoints
│   │   ├── app.py          # FastAPI app setup
│   │   └── routes/
│   │       ├── health.py
│   │       ├── incidents.py
│   │       ├── approvals.py
│   │       ├── agents.py
│   │       ├── monitoring.py
│   │       └── validation.py
│   │
│   ├── dashboard/          # Streamlit UI
│   │   └── app.py
│   │
│   └── main.py             # Application entry point
│
├── tests/                  # 54 pytest tests
├── docs/                   # 20 comprehensive documentation files
├── config/                 # Prometheus configuration
├── contest/                # TCS RIO contest submission materials
│
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── LICENSE                 # Apache 2.0
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
└── SECURITY.md
```

---

## 🧪 Testing

```bash
# Run everything
python -m pytest tests/ -v

# Run a specific test file
python -m pytest tests/test_api.py -v

# Run with coverage report
python -m pytest tests/ --cov=src
```

### Test Breakdown

| Category | Count | What's tested |
|----------|-------|---------------|
| 🧩 Unit | ~30 | Individual agents, services, models |
| 🔗 Integration | ~15 | API routes, pipeline, approval flow |
| 🔄 E2E | ~5 | Full incident lifecycle |
| 💥 Chaos | ~2 | Error handling, timeout recovery |

---

## ⚙️ Configuration

Everything is configurable via environment variables or a `.env` file:

| Prefix | What it configures | Example |
|--------|-------------------|---------|
| `DB_` | PostgreSQL database | `DB_HOST=localhost` |
| `REDIS_` | Redis cache | `REDIS_PORT=6379` |
| `VECTOR_DB_` | Vector database | `VECTOR_DB_PROVIDER=chroma` |
| `LLM_` | LLM provider & model | `LLM_MODEL=gpt-4` |
| `AGENT_` | Agent behavior | `AGENT_DEFAULT_TIMEOUT=300` |
| `SECURITY_` | API keys, secrets | `SECURITY_SECRET_KEY=...` |
| `MONITORING_` | Metrics stack | `MONITORING_PROMETHEUS_URL=...` |
| `INTEGRATION_` | External services | `INTEGRATION_SLACK_ENABLED=true` |

---

## 🗺️ Roadmap

- [ ] **PagerDuty integration** — auto-ingest incidents from PagerDuty webhooks
- [ ] **Slack bot** — respond to incidents right from Slack
- [ ] **Jira ticket creation** — auto-create post-mortem tickets
- [ ] **More agent actions** — k8s rollback, database failover, DNS changes
- [ ] **Multi-LLM support** — Anthropic Claude, Google Gemini, local Ollama
- [ ] **Webhook actions** — trigger external automation workflows
- [ ] **Incident timeline UI** — visual incident timeline in the dashboard
- [ ] **RBAC** — role-based access control for the dashboard & API

---

## 🤝 Contributing

We ❤️ contributions! Whether you're fixing a typo, adding a feature, or improving docs — you're welcome here.

👉 See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

**Quick steps:**

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/awesome-stuff`)
3. Commit your changes (`git commit -m 'feat: add awesome stuff'`)
4. Push (`git push origin feature/awesome-stuff`)
5. Open a Pull Request

---

## 📜 License

This project is licensed under the **Apache License 2.0** — see [LICENSE](LICENSE) for details.

This means you can freely use, modify, and distribute this software, even for commercial purposes. We chose Apache 2.0 because it's a permissive license that also provides patent protection — perfect for welcoming contributions from the community.

---

## 💬 Questions? Ideas? Issues?

| Channel | Purpose |
|---------|---------|
| [🐛 GitHub Issues](https://github.com/jadhav-prathamesh/aegis-incident-response/issues) | Bug reports, feature requests |
| [💬 GitHub Discussions](https://github.com/jadhav-prathamesh/aegis-incident-response/discussions) | Questions, ideas, community support |
| [📖 Documentation](https://github.com/jadhav-prathamesh/aegis-incident-response/tree/master/docs) | In-depth guides, API reference, deployment |

---

<div align="center">
  <sub>Built with ❤️ for the TCS RIO Contest | Made better by the community</sub>
</div>

