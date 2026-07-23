# Regeneration Prompt: Contest Project Summary

## Objective

Regenerate the Contest Project Summary document (`contest/source/Contest_Project_Summary.md`) from the codebase.

## Inputs

- `docs/01_Project_Overview.md` — Summary description
- `docs/11_Project_Structure.md` — Repository structure
- `src/core/config.py` — Application metadata (name, version)
- `pyproject.toml` — Project metadata
- `README.md` — Public description
- `CHANGELOG.md` — Version history

## Generation Instructions

1. Extract app name, version, description from `pyproject.toml` and `src/core/config.py:AppSettings`
2. Count logical lines of Python from `src/` (excluding tests, docs, config)
3. Count test files and test functions from `tests/`
4. List all agent types defined in `src/core/models.py:AgentType`
5. List all action types defined in `src/core/action_dispatcher.py`
6. List all API route files in `src/api/routes/`
7. Count Docker services from `docker-compose.yml`
8. Verify all status labels used are consistent with the Evidence document
9. Output structured document with sections: Overview, Architecture, Components, Status, Evidence

## Verification

- [ ] All numbers match current codebase
- [ ] Agent types match `AgentType` enum
- [ ] Action types match dispatcher registry
- [ ] Repository structure matches actual file tree
