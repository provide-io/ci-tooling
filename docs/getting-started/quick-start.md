# Quick Start

Get up and running with provide.io CI/CD tooling in minutes.

## Option 1: Use Complete CI Workflow (Easiest)

Perfect for most projects - a complete CI/CD pipeline in one step.

### 1. Create Workflow File

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  ci:
    uses: provide-io/ci-tooling/.github/workflows/python-ci.yml@v0.0.1
    with:
      python-version: '3.11'
      coverage-threshold: 80
      run-security: true
```

### 2. Push and Watch

```bash
git add .github/workflows/ci.yml
git commit -m "Add CI workflow"
git push
```

That's it! Your CI pipeline is running:

- ✅ Code quality checks (ruff, mypy)
- ✅ Test execution with coverage
- ✅ Security scanning
- ✅ Package building

## Option 2: Use Individual Actions (Flexible)

For custom workflows, compose individual actions.

### Create Custom Workflow

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python Environment
        uses: provide-io/ci-tooling/actions/setup-python-env@v0.0.1
        with:
          python-version: '3.11'

      - name: Run CI Pipeline
        uses: provide-io/ci-tooling/actions/python-ci@v0.0.1
        with:
          mode: 'full'
          coverage-threshold: 80
          run-quality-checks: true
          run-security-scan: true
```

## Option 3: Add Pre-commit Hooks (Recommended)

Catch issues before commit - saves CI time and provides instant feedback.

### 1. Install Pre-commit

```bash
pip install pre-commit provide-cicd
```

### 2. Configure Hooks

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/provide-io/ci-tooling
    rev: v0.0.1
    hooks:
      - id: provide-conform        # SPDX headers + footers
      - id: provide-config-check   # Config validation
```

### 3. Install Hooks

```bash
pre-commit install
```

### 4. Test It

```bash
# Run on all files
pre-commit run --all-files

# Or just commit - hooks run automatically
git add src/
git commit -m "Add new feature"
```

The hooks will:

- ✅ Add SPDX copyright headers
- ✅ Add repository-specific emoji footers
- ✅ Validate ruff/mypy/pytest configurations

## Complete Example: New Project Setup

Setting up a brand new Python project from scratch:

### 1. Project Structure

```bash
my-project/
├── src/
│   └── my_project/
│       └── __init__.py
├── tests/
│   └── test_example.py
├── pyproject.toml
├── VERSION
├── README.md
└── .github/
    └── workflows/
        └── ci.yml
```

### 2. Create pyproject.toml

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "my-project"
dynamic = ["version"]
requires-python = ">=3.11"
dependencies = []

[dependency-groups]
dev = ["pytest", "pytest-cov", "ruff", "mypy"]

[tool.setuptools]
packages = {find = {where = ["src"]}}

[tool.setuptools.dynamic]
version = {file = "VERSION"}

[tool.ruff]
line-length = 111
target-version = "py311"

[tool.mypy]
python_version = "3.11"
mypy_path = "src"
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src", "."]
```

### 3. Create VERSION File

```bash
echo "0.1.0" > VERSION
```

### 4. Add CI Workflow

`.github/workflows/ci.yml`:

```yaml
name: CI

on: [push, pull_request]

jobs:
  ci:
    uses: provide-io/ci-tooling/.github/workflows/python-ci.yml@v0.0.1
    with:
      python-version: '3.11'
```

### 5. Add Pre-commit Hooks

`.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/provide-io/ci-tooling
    rev: v0.0.1
    hooks:
      - id: provide-conform
      - id: provide-config-check
```

Install:

```bash
pip install pre-commit provide-cicd
pre-commit install
pre-commit run --all-files
```

### 6. Push to GitHub

```bash
git init
git add .
git commit -m "Initial project setup"
git remote add origin https://github.com/yourorg/my-project.git
git push -u origin main
```

Done! Your project now has:

- ✅ Automated CI/CD pipeline
- ✅ Pre-commit quality checks
- ✅ Standardized configuration
- ✅ Test coverage tracking

## Testing Actions Locally

You can test individual hooks before committing:

### Test provide-conform

```bash
provide-conform src/**/*.py
```

### Test provide-config-check

```bash
provide-config-check pyproject.toml
```

### Run All Pre-commit Hooks

```bash
pre-commit run --all-files
```

## Common Workflows

### Run Tests Only

```yaml
- uses: provide-io/ci-tooling/actions/python-ci@v0.0.1
  with:
    mode: 'test'
    coverage-threshold: 80
```

### Build Package Only

```yaml
- uses: provide-io/ci-tooling/actions/python-ci@v0.0.1
  with:
    mode: 'build'
```

### Quality Checks Only

```yaml
- uses: provide-io/ci-tooling/actions/python-ci@v0.0.1
  with:
    mode: 'quality'
```

## Matrix Testing

Test across multiple Python versions and operating systems:

```yaml
jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ['3.11', '3.12', '3.13']

    runs-on: ${{ matrix.os }}

    steps:
      - uses: actions/checkout@v4

      - uses: provide-io/ci-tooling/actions/python-ci@v0.0.1
        with:
          python-version: ${{ matrix.python-version }}
```

## Troubleshooting

### Hooks Not Running

```bash
# Reinstall hooks
pre-commit uninstall
pre-commit install

# Clear cache
pre-commit clean
```

### Action Failures

Check GitHub Actions logs for detailed error messages. Common issues:

- Missing `workenv/` directory - use `setup-python-env` action first
- Missing dependencies - ensure `pyproject.toml` has correct `[dependency-groups]`
- Coverage threshold - adjust `coverage-threshold` input

## Next Steps

- [Actions Reference](../actions/index/) - Detailed action documentation
- [Workflows Reference](../workflows/index/) - Reusable workflow examples
- [Pre-commit Hooks](../pre-commit-hooks/) - Hook configuration details
- [Design Documents](../ci-orchestrator-design/) - Architecture details
