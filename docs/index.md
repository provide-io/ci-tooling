# CI/CD Tooling

Shared GitHub Actions, reusable workflows, and pre-commit hooks for Python projects in the provide.io ecosystem.

## Overview

The provide.io CI/CD Tooling provides standardized, battle-tested components for Python project automation:

- **GitHub Actions** - Reusable composite actions for common CI/CD tasks
- **Workflows** - Complete CI/CD pipelines as reusable workflows
- **Pre-commit Hooks** - Code quality enforcement at commit time

## Features

### 🚀 GitHub Actions

**Composite actions for flexible CI/CD pipelines:**

- [`setup-python-env`](actions/setup-python-env/) - Python, UV, and workenv setup
- [`python-ci`](actions/python-ci/) - Complete CI pipeline (quality + tests + build)
- [`python-release`](actions/python-release/) - PyPI publishing and GitHub releases

### 🔄 Reusable Workflows

**Complete end-to-end workflows:**

- [`python-ci.yml`](workflows/python-ci/) - Continuous Integration workflow
- [`python-release.yml`](workflows/python-release/) - Release automation workflow

### 🔍 Pre-commit Hooks

**Automatic code quality enforcement:**

- `provide-conform` - SPDX headers and emoji footers (auto-detects repository)
- `provide-config-check` - Validates ruff/mypy/pytest configurations

## Quick Start

### Using Actions

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run CI Pipeline
        uses: provide-io/ci-tooling/actions/python-ci@v0.0.1
        with:
          python-version: '3.11'
          coverage-threshold: 80
```

### Using Reusable Workflows

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  ci:
    uses: provide-io/ci-tooling/.github/workflows/python-ci.yml@v0.0.1
    with:
      python-version: '3.11'
      run-security: true
```

### Using Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/provide-io/ci-tooling
    rev: v0.0.1
    hooks:
      - id: provide-conform
      - id: provide-config-check
```

## Installation

### Install Pre-commit Hooks Package

```bash
# Using pip
pip install provide-cicd

# Using uv
uv pip install provide-cicd
```

### Set Up Pre-commit in Your Project

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml (see above)
# Install hooks
pre-commit install
```

## Documentation Structure

- **[Getting Started](getting-started/installation/)** - Installation and setup guide
- **[Actions](actions/index/)** - Individual GitHub Actions reference
- **[Workflows](workflows/index/)** - Reusable workflow documentation
- **[Pre-commit Hooks](pre-commit-hooks/)** - Pre-commit hook configuration
- **[Design Documents](ci-orchestrator-design/)** - Architecture and design decisions

## Design Philosophy

### Convention Over Configuration

The tooling follows ecosystem conventions:

- Source code in `src/` directory
- Tests in `tests/` directory
- Use `workenv/` not `.venv` for virtual environments
- Python 3.11+ as minimum version
- UV as package manager
- Ruff for linting and formatting
- MyPy for type checking

### Progressive Enhancement

Start simple and add features as needed:

1. **Basic**: Use `python-ci` action for complete pipeline
2. **Custom**: Compose individual actions for custom workflows
3. **Advanced**: Extend with additional steps and matrix testing

### Zero-Friction Developer Experience

- **Auto-detection**: `provide-conform` automatically detects repository
- **Sensible defaults**: All actions work with minimal configuration
- **Clear feedback**: Rich GitHub step summaries and error messages

## Package Information

- **PyPI Package**: `provide-cicd`
- **Import Path**: `from provide.cicd import ...`
- **GitHub Repository**: [provide-io/ci-tooling](https://github.com/provide-io/ci-tooling)
- **Documentation**: [foundry.provide.io/cicd](https://foundry.provide.io/cicd/)

## Support

- **Issues**: [GitHub Issues](https://github.com/provide-io/ci-tooling/issues)
- **Discussions**: [GitHub Discussions](https://github.com/provide-io/ci-tooling/discussions)
- **Documentation**: This site

## License

Apache-2.0 - Copyright (c) 2025 provide.io llc
