# provide.io CI Tooling

Shared GitHub Actions and reusable workflows for provide.io projects.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![GitHub release](https://img.shields.io/github/release/provide-io/ci-tooling.svg)](https://github.com/provide-io/ci-tooling/releases)

## Key Features
Key features are highlighted in the sections below and in the documentation.

## 🚀 Quick Start

### Using Individual Actions

```yaml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: provide-io/ci-tooling/actions/setup-python-env@v0
        with:
          python-version: '3.11'

      - uses: provide-io/ci-tooling/actions/python-ci@v0
        with:
          coverage-threshold: 80
```

### Using Reusable Workflows

```yaml
name: CI
on: [push, pull_request]

jobs:
  ci:
    uses: provide-io/ci-tooling/.github/workflows/python-ci.yml@v0
    with:
      python-version: '3.11'
      matrix-testing: true
      run-security: true
    secrets:
      CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}
```

## Documentation
Documentation is currently captured in this README.

## Development
Development notes are in [CLAUDE.md](CLAUDE.md).

## 🤝 Contributing

We welcome contributions! Please see [CLAUDE.md](./CLAUDE.md) for local development guidance.

### Development Setup

```bash
git clone https://github.com/provide-io/ci-tooling.git
cd ci-tooling

# Test actions locally
./scripts/test-actions.sh

# Validate workflows
./scripts/validate-workflows.sh
```

## 📄 License

Licensed under the Apache License, Version 2.0. See [LICENSE](./LICENSE) for details.

---

**provide.io llc** - Simplifying CI/CD for Python projects

## 📦 Available Actions

### Core Actions

| Action | Description | Documentation |
|--------|-------------|---------------|
| [`setup-python-env`](./actions/setup-python-env/) | Setup Python, UV, and workenv | [action.yml](./actions/setup-python-env/action.yml) |
| [`setup-github-auth`](./actions/setup-github-auth/) | Configure GitHub authentication | [README](./actions/setup-github-auth/README.md) |
| [`python-ci`](./actions/python-ci/) | Combined lint, test, and build pipeline | [action.yml](./actions/python-ci/action.yml) |
| [`python-release`](./actions/python-release/) | PyPI publishing | [action.yml](./actions/python-release/action.yml) |
| [`run-ci-tasks`](./actions/run-ci-tasks/) | Run repo-specific CI tasks | [action.yml](./actions/run-ci-tasks/action.yml) |
| [`build-psp`](./actions/build-psp/) | Build PSP artifacts | [action.yml](./actions/build-psp/action.yml) |

### Reusable Workflows

| Workflow | Description | Documentation |
|----------|-------------|---------------|
| [`python-ci.yml`](./.github/workflows/python-ci.yml) | Complete CI pipeline | [workflow](./.github/workflows/python-ci.yml) |
| [`python-release.yml`](./.github/workflows/python-release.yml) | Release workflow | [workflow](./.github/workflows/python-release.yml) |

## 🏗️ Architecture

```
provide-io/ci-tooling/
├── .github/workflows/        # Reusable workflows
│   ├── python-ci.yml         # CI pipeline
│   └── python-release.yml    # Release pipeline
├── actions/                  # Composite actions
│   ├── build-psp/            # Build PSP artifacts
│   ├── python-ci/            # Lint, test, build pipeline
│   ├── python-release/       # Publishing
│   ├── run-ci-tasks/         # Repo-specific CI hooks
│   ├── setup-github-auth/    # GitHub auth setup
│   └── setup-python-env/     # Environment setup
├── configs/                  # Action configuration
├── scripts/                  # Utility scripts
└── templates/                # Project templates
```

## 🔧 Migration Guide

### From Custom CI to Shared Actions

1. **Identify your current workflow patterns**
2. **Choose the appropriate approach**:
   - Individual actions for granular control
   - Reusable workflows for standardization
3. **Update your `.github/workflows/` files**
4. **Test thoroughly**

### Example Migration

**Before** (custom workflow):
```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install UV
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      - name: Install deps
        run: uv pip install -e ".[dev]"
      - name: Run ruff
        run: ruff check src/
      - name: Run tests
        run: pytest
```

**After** (using shared actions):
```yaml
name: CI
on: [push, pull_request]
jobs:
  ci:
    uses: provide-io/ci-tooling/.github/workflows/python-ci.yml@v0
    with:
      python-version: '3.11'
```

## 📋 Project Templates

Ready-to-use workflow templates for different project types:

- **[Basic Python](./templates/basic-python/)** - Simple Python package
- **[Terraform Provider](./templates/terraform-provider/)** - Provider with tests
- **[Full Featured](./templates/full-featured/)** - Complete CI/CD with security

## 🔄 Versioning

This repository uses semantic versioning:

- `v0` - Latest development (may have breaking changes)
- `v0.1` - Specific minor version
- `v0.1.0` - Exact version

**Recommendation**: Use `v0` for latest features, pin to specific versions for stability.

## 📖 Reference

- [Actions](./actions/)
- [Workflows](./.github/workflows/)
- [Templates](./templates/)

## 🆘 Support

- 🐛 [Issue Tracker](https://github.com/provide-io/ci-tooling/issues)
- 💬 [Discussions](https://github.com/provide-io/ci-tooling/discussions)
