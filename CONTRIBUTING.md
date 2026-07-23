# 🤝 Contributing to Aegis

First off, thank you for considering contributing to Aegis! We genuinely appreciate every contribution — whether it's fixing a typo, improving documentation, reporting a bug, or submitting a feature request.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Guidelines](#coding-guidelines)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Questions?](#questions)

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). By participating, you're expected to uphold this code. Please report unacceptable behavior to the maintainers.

## How Can I Contribute?

### 🐛 Report a Bug

Found something broken? Open an issue using the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md). The more details you provide (logs, steps to reproduce, environment), the faster we can fix it.

### 💡 Suggest a Feature

Got an idea to make Aegis better? Open a [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md). Tell us what problem you're trying to solve, not just what you want built.

### 📝 Improve Documentation

Good documentation makes great software. If you find something unclear, missing, or just plain wrong — fix it! Documentation lives in the `docs/` directory and the `README.md`.

### 🚀 Submit Code

Bug fixes, performance improvements, new agent capabilities, integrations — all are welcome! Check the [open issues](https://github.com/jadhav-prathamesh/aegis-incident-response/issues) for something tagged `good first issue` or `help wanted`.

## Getting Started

1. **Fork the repo** — click the Fork button on GitHub
2. **Clone your fork**:
   ```bash
   git clone https://github.com/your-username/aegis-incident-response.git
   cd aegis-incident-response
   ```
3. **Set up the development environment**:
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   pip install -e ".[dev]"
   ```
4. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

1. **Write code** — make your changes
2. **Write/update tests** — we aim for >80% coverage
3. **Run tests** — make sure everything passes:
   ```bash
   python -m pytest tests/ -v
   ```
4. **Format your code** — we use Ruff:
   ```bash
   ruff format src/ tests/
   ruff check --fix src/ tests/
   ```
5. **Run type checking**:
   ```bash
   mypy src/
   ```
6. **Commit** — use clear commit messages:
   ```
   feat(agent): add rollback capability to Executor
   fix(api): handle null incident descriptions in GET response
   docs: clarify configuration env var prefixes
   ```

## Coding Guidelines

### Python Style

- **Python 3.12+** — use modern Python features (pattern matching, type unions with `|`)
- **Type hints everywhere** — all functions must have type annotations
- **Follow PEP 8** — enforced by Ruff with the project's `pyproject.toml` config
- **Docstrings** — use Google-style docstrings for public APIs
- **No print statements** — use `structlog` for logging

### Agent Design

- Each agent extends `BaseAgent` from `src/agents/base.py`
- Agents communicate via the orchestrator, not directly
- Keep agent logic focused — one responsibility per agent
- Use LangGraph for agent workflow graphs

### API Design

- Follow RESTful conventions
- Use Pydantic models for request/response schemas
- Return appropriate HTTP status codes
- Include error details in responses

## Testing

- **All new features must include tests**
- Run the full suite before submitting:
  ```bash
  python -m pytest tests/ -v --cov=src
  ```
- Test categories:
  - `pytest -m unit` — unit tests
  - `pytest -m integration` — integration tests
  - `pytest -m e2e` — end-to-end tests

## Pull Request Process

1. **Update your fork** to the latest upstream main:
   ```bash
   git remote add upstream https://github.com/jadhav-prathamesh/aegis-incident-response.git
   git fetch upstream
   git rebase upstream/main
   ```
2. **Push your branch**:
   ```bash
   git push origin feature/your-feature-name
   ```
3. **Open a Pull Request** — use the [PR template](.github/PULL_REQUEST_TEMPLATE.md)
4. **Address review feedback** — maintainers may request changes
5. **Merge** — once approved, a maintainer will merge your PR

### PR Checklist

- [ ] Tests pass (`python -m pytest tests/ -v`)
- [ ] New tests added for new functionality
- [ ] Code formatted with Ruff
- [ ] Type checks pass (`mypy src/`)
- [ ] Documentation updated (if needed)
- [ ] CHANGELOG.md updated (if applicable)

## Questions?

- Open a [Discussion](https://github.com/jadhav-prathamesh/aegis-incident-response/discussions)
- Check the [Documentation](docs/) for detailed guides

---

**Thank you for contributing!** 🎉 Your effort makes incident response better for everyone.

