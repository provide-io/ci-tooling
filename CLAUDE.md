# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is the provide.io CI Tooling repository - a collection of reusable GitHub Actions and workflows for Python projects. The repository provides standardized CI/CD patterns used across provide.io projects.

## Architecture

The repository is organized into these key components:

### Actions (`actions/`)
Composite GitHub Actions that handle specific CI tasks:
- `setup-python-env/` - Environment setup with Python, UV, and workenv (not .venv)
- `python-quality/` - Code quality checks with ruff and mypy
- `python-test/` - Test execution with pytest and coverage
- `python-security/` - Security scanning with bandit/safety
- `python-build/` - Package building for PyPI
- `python-release/` - PyPI publishing with official PyPA action

### Workflows (`.github/workflows/`)
Reusable workflow files:
- `python-ci.yml` - Complete CI pipeline (quality → tests → security → performance)
- `python-release.yml` - Release pipeline with automated PyPI publishing
- `test-actions.yml` - Internal testing of the actions themselves

### Templates & Examples
- `templates/` - Project template configurations
- `examples/` - Test cases and usage examples including matrix-testing, minimal-setup, monorepo, multi-package

## Environment Setup

This repository uses:
- **UV package manager** (not pip) for dependency management
- **workenv/** directory (not .venv) for virtual environments
- **Python 3.11+** as the minimum version
- **pyproject.toml** for project configuration

## Development Commands

### Testing Actions Locally
```bash
# Test example configurations
pytest examples/

# Test individual actions (manual GitHub Actions runner required)
```

### Code Quality
Actions in this repository implement these quality standards:
- **ruff** for linting and formatting
- **mypy** for type checking
- **pytest** for testing with coverage
- **bandit/safety** for security scanning

### Project Structure Patterns
Actions expect Python projects to follow these conventions:
- Source code in `src/` directory
- Tests in `tests/` directory
- Configuration in `pyproject.toml`
- Optional development dependencies as `[dev]` extras

## Key Implementation Details

### Environment Strategy
- All actions use `workenv/` for virtual environments (configured in setup-python-env action)
- UV is used for fast dependency installation
- PYTHONPATH is automatically configured for src/ directory imports

### Workflow Dependencies
The python-ci.yml workflow runs jobs in this order:
1. **quality** - Linting, formatting, type checking
2. **test** - Unit tests with coverage (runs after quality passes)
3. **security** - Security scanning (runs parallel to tests)
4. **performance** - Optional performance benchmarks

### Coverage and Reporting
- Coverage threshold defaults to 80%
- XML reports generated for external services (Codecov)
- GitHub step summaries provide detailed reports
- SARIF files uploaded for security results

## Action Usage Patterns

### Individual Actions
```yaml
- uses: provide-io/ci-tooling/actions/setup-python-env@v0.0.1
  with:
    python-version: '3.11'
    install-extras: 'dev,test'
```

### Reusable Workflows
```yaml
jobs:
  ci:
    uses: provide-io/ci-tooling/workflows/python-ci.yml@v0.0.1
    with:
      python-version: '3.11'
      matrix-testing: true
      run-security: true
```

## Important Notes

- Use `v0.0.1` tag for the current stable version
- Pin to specific versions for stability
- All actions support customizable source/test paths
- Matrix testing supports multiple Python versions and OS
- Security scanning requires `security-events: write` permissions