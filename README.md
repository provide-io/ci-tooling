# provide.io CI Tooling

Shared GitHub Actions and reusable workflows for provide.io projects.

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT) [![GitHub release](https://img.shields.io/github/release/provide-io/ci-tooling.svg)](https://github.com/provide-io/ci-tooling/releases)

## Key Features

- Shared composite actions for Python CI workflows.
- Reusable workflows for standardized pipeline setups.
- Project templates and scripts for consistent automation.

## Key Features

- Shared composite actions for Python CI workflows.
- Reusable workflows for standardized pipeline setups.
- Project templates and scripts for consistent automation.

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

- [Actions](https://github.com/provide-io/ci-tooling/tree/main/actions)
- [Workflows](https://github.com/provide-io/ci-tooling/tree/main/.github/workflows)
- [Templates](https://github.com/provide-io/ci-tooling/tree/main/templates)

## Development

- See [CLAUDE.md](https://github.com/provide-io/ci-tooling/blob/main/CLAUDE.md) for local development notes.
- Run `./scripts/test-actions.sh` to validate actions locally.

## 🤝 Contributing

We welcome contributions! Please see [CLAUDE.md](https://github.com/provide-io/ci-tooling/blob/main/CLAUDE.md) for local development guidance.

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

Licensed under the Apache License, Version 2.0. See [LICENSE](https://github.com/provide-io/ci-tooling/blob/main/LICENSE) for details.

______________________________________________________________________

**provide.io llc** - Simplifying CI/CD for Python projects

## 📦 Available Actions

- [Actions](https://github.com/provide-io/ci-tooling/tree/main/actions)
- [Workflows](https://github.com/provide-io/ci-tooling/tree/main/.github/workflows)
- [Templates](https://github.com/provide-io/ci-tooling/tree/main/templates)

| Action                                                                                              | Description                             | Documentation                                                                                        |
| --------------------------------------------------------------------------------------------------- | --------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| [`setup-python-env`](https://github.com/provide-io/ci-tooling/tree/main/actions/setup-python-env)   | Setup Python, UV, and workenv           | [action.yml](https://github.com/provide-io/ci-tooling/blob/main/actions/setup-python-env/action.yml) |
| [`setup-github-auth`](https://github.com/provide-io/ci-tooling/tree/main/actions/setup-github-auth) | Configure GitHub authentication         | [README](https://github.com/provide-io/ci-tooling/blob/main/actions/setup-github-auth/README.md)     |
| [`python-ci`](https://github.com/provide-io/ci-tooling/tree/main/actions/python-ci)                 | Combined lint, test, and build pipeline | [action.yml](https://github.com/provide-io/ci-tooling/blob/main/actions/python-ci/action.yml)        |
| [`python-release`](https://github.com/provide-io/ci-tooling/tree/main/actions/python-release)       | PyPI publishing                         | [action.yml](https://github.com/provide-io/ci-tooling/blob/main/actions/python-release/action.yml)   |
| [`run-ci-tasks`](https://github.com/provide-io/ci-tooling/tree/main/actions/run-ci-tasks)           | Run repo-specific CI tasks              | [action.yml](https://github.com/provide-io/ci-tooling/blob/main/actions/run-ci-tasks/action.yml)     |
| [`build-psp`](https://github.com/provide-io/ci-tooling/tree/main/actions/build-psp)                 | Build PSP artifacts                     | [action.yml](https://github.com/provide-io/ci-tooling/blob/main/actions/build-psp/action.yml)        |

### Reusable Workflows

| Workflow                                                                                                        | Description          | Documentation                                                                                       |
| --------------------------------------------------------------------------------------------------------------- | -------------------- | --------------------------------------------------------------------------------------------------- |
| [`python-ci.yml`](https://github.com/provide-io/ci-tooling/blob/main/.github/workflows/python-ci.yml)           | Complete CI pipeline | [workflow](https://github.com/provide-io/ci-tooling/blob/main/.github/workflows/python-ci.yml)      |
| [`python-release.yml`](https://github.com/provide-io/ci-tooling/blob/main/.github/workflows/python-release.yml) | Release workflow     | [workflow](https://github.com/provide-io/ci-tooling/blob/main/.github/workflows/python-release.yml) |

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
1. **Choose the appropriate approach**:
   - Individual actions for granular control
   - Reusable workflows for standardization
1. **Update your `.github/workflows/` files**
1. **Test thoroughly**

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

- **[Basic Python](https://github.com/provide-io/ci-tooling/tree/main/templates/basic-python)** - Simple Python package
- **[Terraform Provider](https://github.com/provide-io/ci-tooling/tree/main/templates/terraform-provider)** - Provider with tests
- **[Full Featured](https://github.com/provide-io/ci-tooling/tree/main/templates/full-featured)** - Complete CI/CD with security

## 🔄 Versioning

This repository uses semantic versioning:

- `v0` - Latest development (may have breaking changes)
- `v0.1` - Specific minor version
- `v0.1.0` - Exact version

**Recommendation**: Use `v0` for latest features, pin to specific versions for stability.

## 📖 Reference

- [Actions](https://github.com/provide-io/ci-tooling/tree/main/actions)
- [Workflows](https://github.com/provide-io/ci-tooling/tree/main/.github/workflows)
- [Templates](https://github.com/provide-io/ci-tooling/tree/main/templates)

## 🆘 Support

- 🐛 [Issue Tracker](https://github.com/provide-io/ci-tooling/issues)
- 💬 [Discussions](https://github.com/provide-io/ci-tooling/discussions)

Copyright (c) Provide.io LLC.
