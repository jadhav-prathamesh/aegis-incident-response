# Aegis — "Multi-Agent AI Incident Response Platform"
## Testing

## Purpose

Document the testing strategy, test structure, coverage, and how to run tests.

## Source Traceability

| Component | File(s) |
|---|---|
| Test configuration | `pyproject.toml` (pytest section) |
| Action dispatcher tests | `tests/test_action_dispatcher.py` |
| Agent orchestrator tests | `tests/test_agent_orchestrator.py` |
| Agent pipeline tests | `tests/test_agent_pipeline.py` |
| API tests | `tests/test_api.py` |
| Approval tests | `tests/test_approval.py` |
| Dashboard tests | `tests/test_dashboard.py` |
| Planner search tests | `tests/test_planner_search.py` |
| Similar incident tests | `tests/test_similar_incidents.py` |

## Test Summary

| File | Tests | Type | What It Tests |
|---|---|---|---|
| `test_action_dispatcher.py` | 8 | Unit | Action dispatch, dry-run, individual handlers |
| `test_agent_orchestrator.py` | 26 | Behavioural | Fallback decisions, should_continue, execute_decision, process_task |
| `test_agent_pipeline.py` | 28 | Behavioural | Observer status/recommendations, executor steps, validator, planner |
| `test_api.py` | 8 | Integration (mocked) | Health, incidents CRUD, approvals, agents |
| `test_approval.py` | 6 | Unit | Approval lifecycle, auto-approve, requires_approval |
| `test_dashboard.py` | 6 | Unit | Severity/status colors, enum_val, incident indexing |
| `test_planner_search.py` | 3 | Unit | Knowledge base search, vector DB fallback, PromQL |
| `test_similar_incidents.py` | 3 | Unit | Similarity search ranking, empty results |
| **Total** | **93** | — | — |

## Test Configuration

From `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--tb=short",
    "-ra",
    "--timeout=60",
]
```

Markers available: unit, integration, e2e, contract, chaos, load, slow.

## Running Tests

### All tests

```bash
python -m pytest tests/ -v
```

### Specific file

```bash
python -m pytest tests/test_api.py -v
```

### With coverage

```bash
python -m pytest tests/ --cov=src
```

Coverage configuration: source = `src`, branch coverage enabled, excludes tests/scripts/migrations.

## Testing Approach

### Unit Tests
Test pure logic in isolation:
- `test_approval.py` — Approval request state transitions, auto-approve logic
- `test_dashboard.py` — Color mapping, enum conversion
- `test_action_dispatcher.py` — Individual action handler behaviour
- `test_planner_search.py` — Knowledge base fallback, vector DB integration

### Behavioural Tests
Test agent decision logic without LLM:
- `test_agent_orchestrator.py` — Orchestrator fallback decisions, should_continue logic, execute_decision, process_task flows. LLM calls are mocked.
- `test_agent_pipeline.py` — Observer status determination, recommendations, executor step processing, approval flow, validator checks, planner context building

### Integration Tests (mocked)
Test API endpoints with mocked service calls:
- `test_api.py` — Health, incident CRUD, approvals, agents

## Mocking Strategy

- LLM calls: Mocked using `@patch` on `_call_llm` or `_make_decision` to return predefined responses
- External services: Action dispatcher tests mock `_run_command`
- Vector DB: Knowledge base tests provide mock vector DB or use seed corpus fallback
- Database: Not used in tests (incident store is in-memory)

## CI/CD

**Not implemented** — no CI/CD pipeline configuration exists in the repository. GitHub Actions or similar would need to be added.

## Coverage Status

Coverage targets are not enforced in `pyproject.toml`. The coverage configuration (`[tool.coverage]`) is present but optional — coverage reports can be generated but no minimum threshold is set.
