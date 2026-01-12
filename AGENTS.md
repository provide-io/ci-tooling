# AGENTS.md

This file provides guidance for AI assistants when working with code in this repository.

## Repository Overview

This is the provide.io CI Tooling repository - a collection of reusable GitHub Actions and workflows for Python projects. The repository provides standardized CI/CD patterns used across provide.io projects.

**Note**: The Python CLI tools (`provide-conform`, `provide-config-check`) have been moved to `wrknv`. Use `wrknv conform` and `wrknv config-check` instead.

## Architecture

The repository is organized into these key components:

### Actions (`actions/`)
Composite GitHub Actions that handle specific CI tasks:
- `setup-python-env/` - Environment setup with Python, UV, and .venv
- `python-quality/` - Code quality checks with ruff and mypy
- `python-test/` - Test execution with pytest and coverage
- `python-security/` - Security scanning with bandit/safety
- `python-build/` - Package building for PyPI
- `python-release/` - PyPI publishing with official PyPA action

### Workflows (`.github/workflows/`)
Reusable workflow files:
- `python-ci.yml` - Complete CI pipeline (quality -> tests -> security -> performance)
- `python-release.yml` - Release pipeline with automated PyPI publishing
- `test-actions.yml` - Internal testing of the actions themselves

### Templates & Examples
- `templates/` - Project template configurations
- `examples/` - Test cases and usage examples including matrix-testing, minimal-setup, monorepo, multi-package

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
