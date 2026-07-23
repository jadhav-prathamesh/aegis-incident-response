# Changelog

## Unreleased

### Added
- Streamlit Dashboard — incident viewing, RCA overview, approval management, incident creation
- Dashboard tests (6 tests)
- Dashboard service in docker-compose.yml (port 8501)
- Comprehensive README with architecture, API docs, configuration reference

### Fixed
- config.py: pydantic-settings nested BaseSettings env var collision (AGENT=1)
- similar_incidents.py: enum.value compatibility with use_enum_values=True
- incidents.py routes: enum.value compatibility
- agents.py routes: enum.value compatibility
- approval.py: requires_approval() logic (FLUSH_QUEUE/SCALE_DOWN always require)
- test_similar_incidents.py: test_incident_to_searchable category mismatch

### Changed
- Tests: 29/29 → 39/39 passing

## Previous

- Established project resume documentation
- Package structure, base agent fixes, orchestrator compatibility
- Incident store, logging fallback, agent factory smoke validation
- Validator flow, executor smoke tests, import validation
