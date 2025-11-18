# provide.io CI Tooling

Shared GitHub Actions and reusable workflows for provide.io projects.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![GitHub release](https://img.shields.io/github/release/provide-io/ci-tooling.svg)](https://github.com/provide-io/ci-tooling/releases)

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

      - uses: provide-io/ci-tooling/actions/python-quality@v0

      - uses: provide-io/ci-tooling/actions/python-test@v0
        with:
          coverage-threshold: 80
```

### Using Reusable Workflows

```yaml
name: CI
on: [push, pull_request]

jobs:
  ci:
    uses: provide-io/ci-tooling/workflows/python-ci.yml@v0
    with:
      python-version: '3.11'
      matrix-testing: true
      run-security: true
    secrets:
      CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}
```

## 📦 Available Actions

### Core Actions

| Action | Description | Documentation |
|--------|-------------|---------------|
| [`setup-python-env`](./actions/setup-python-env/) | Setup Python, UV, and workenv | [README](./actions/setup-python-env/README.md) |
| [`python-quality`](./actions/python-quality/) | Code quality with ruff and mypy | [README](./actions/python-quality/README.md) |
| [`python-test`](./actions/python-test/) | Test execution with pytest | [README](./actions/python-test/README.md) |
| [`python-security`](./actions/python-security/) | Security scanning | [README](./actions/python-security/README.md) |
| [`python-build`](./actions/python-build/) | Package building | [README](./actions/python-build/README.md) |
| [`python-release`](./actions/python-release/) | PyPI publishing | [README](./actions/python-release/README.md) |

### Reusable Workflows

| Workflow | Description | Documentation |
|----------|-------------|---------------|
| [`python-ci.yml`](./workflows/python-ci.yml) | Complete CI pipeline | [README](./docs/workflows/python-ci.md) |
| [`python-release.yml`](./workflows/python-release.yml) | Release workflow | [README](./docs/workflows/python-release.md) |

## 🏗️ Architecture

```
provide-io/ci-tooling/
├── actions/                  # Composite actions
│   ├── setup-python-env/     # Environment setup
│   ├── python-quality/       # Code quality
│   ├── python-test/          # Testing
│   ├── python-security/      # Security scanning
│   ├── python-build/         # Package building
│   └── python-release/       # Publishing
├── workflows/                # Reusable workflows
│   ├── python-ci.yml         # CI pipeline
│   └── python-release.yml    # Release pipeline
├── scripts/                  # Utility scripts
├── templates/                # Project templates
└── docs/                     # Documentation
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
    uses: provide-io/ci-tooling/workflows/python-ci.yml@v0
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

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](./CONTRIBUTING.md) for details.

### Development Setup

```bash
git clone https://github.com/provide-io/ci-tooling.git
cd ci-tooling

# Test actions locally
./scripts/test-actions.sh

# Validate workflows
./scripts/validate-workflows.sh
```

## 📖 Documentation

- [Getting Started Guide](./docs/getting-started.md)
- [Migration Guide](./docs/migration-guide.md)
- [Action Reference](./docs/actions/)
- [Workflow Reference](./docs/workflows/)
- [Best Practices](./docs/best-practices.md)

## 🆘 Support

- 📖 [Documentation](./docs/)
- 🐛 [Issue Tracker](https://github.com/provide-io/ci-tooling/issues)
- 💬 [Discussions](https://github.com/provide-io/ci-tooling/discussions)

## 📄 License

Licensed under the Apache License, Version 2.0. See [LICENSE](./LICENSE) for details.

---

**provide.io llc** - Simplifying CI/CD for Python projects