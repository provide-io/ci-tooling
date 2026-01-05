# Installation

How to install and set up provide.io CI/CD tooling in your project.

## Install Pre-commit Hooks Package

The `provide-cicd` package provides pre-commit hooks for code quality enforcement.

### Using pip

```bash
pip install provide-cicd
```

### Using UV (Recommended)

```bash
uv pip install provide-cicd
```

### As Development Dependency

Add to your `pyproject.toml`:

```toml
[dependency-groups]
dev = [
    "provide-cicd",
]
```

Then install:

```bash
uv sync
```

## Install Pre-commit Framework

If you don't have pre-commit installed:

```bash
# Using pip
pip install pre-commit

# Using UV
uv pip install pre-commit
```

## Configure Pre-commit Hooks

Create `.pre-commit-config.yaml` in your project root:

```yaml
repos:
  - repo: https://github.com/provide-io/ci-tooling
    rev: v0.0.1  # Use the latest release tag
    hooks:
      - id: provide-conform
      - id: provide-config-check
```

Install the hooks:

```bash
pre-commit install
```

## Using GitHub Actions

No installation required! GitHub Actions are referenced directly in workflow files.

### Pin to Specific Version

```yaml
- uses: provide-io/ci-tooling/actions/python-ci@v0.0.1
```

### Use Latest Release

```yaml
- uses: provide-io/ci-tooling/actions/python-ci@main
```

**Note**: Pinning to a specific version (e.g., `@v0.0.1`) is recommended for stability.

## Using Reusable Workflows

Reference workflows directly from your workflow files:

```yaml
jobs:
  ci:
    uses: provide-io/ci-tooling/.github/workflows/python-ci.yml@v0.0.1
```

## Verification

### Verify Pre-commit Hooks

Test the hooks manually:

```bash
# Run hooks on all files
pre-commit run --all-files

# Run hooks on staged files
pre-commit run
```

### Verify Entry Points

Check that command-line tools are available:

```bash
provide-conform --help
provide-config-check --help
```

## Upgrading

### Upgrade Pre-commit Hooks Package

```bash
# Using pip
pip install --upgrade provide-cicd

# Using UV
uv pip install --upgrade provide-cicd
```

### Update Pre-commit Hook Versions

Update the `rev` in `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/provide-io/ci-tooling
    rev: v0.0.2  # Update to new version
    hooks:
      - id: provide-conform
      - id: provide-config-check
```

Then update pre-commit:

```bash
pre-commit autoupdate
```

### Update GitHub Actions

Update version tags in workflow files:

```yaml
# Before
- uses: provide-io/ci-tooling/actions/python-ci@v0.0.1

# After
- uses: provide-io/ci-tooling/actions/python-ci@v0.0.2
```

## Requirements

- **Python**: 3.11 or higher
- **UV**: 0.7.8 or higher (for actions)
- **Git**: For pre-commit hooks
- **GitHub**: For GitHub Actions

## Next Steps

- [Quick Start Guide](../getting-started/quick-start/) - Get up and running quickly
- [Actions Documentation](../actions/) - Learn about individual actions
- [Workflows Documentation](../workflows/) - Complete workflow examples
- [Pre-commit Hooks](../pre-commit-hooks/) - Detailed hook configuration
