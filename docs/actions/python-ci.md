# python-ci

Comprehensive Python CI pipeline with quality checks, testing, security scanning, and building.

## Overview

This composite action provides a complete CI pipeline for Python projects:

- **Code Quality**: Ruff linting and formatting, MyPy type checking
- **Testing**: PyTest execution with coverage tracking
- **Security**: Bandit security scanning
- **Building**: Package building with UV
- **Artifacts**: Automatic upload of test results and packages

## Usage

### Full Pipeline (Default)

```yaml
- name: Run CI Pipeline
  uses: provide-io/ci-tooling/actions/python-ci@v0.0.1
  with:
    python-version: '3.11'
    coverage-threshold: 80
```

### Test Only

```yaml
- name: Run Tests
  uses: provide-io/ci-tooling/actions/python-ci@v0.0.1
  with:
    mode: 'test'
    coverage-threshold: 80
```

### Build Only

```yaml
- name: Build Package
  uses: provide-io/ci-tooling/actions/python-ci@v0.0.1
  with:
    mode: 'build'
```

### With Security Scanning

```yaml
- name: Run CI with Security
  uses: provide-io/ci-tooling/actions/python-ci@v0.0.1
  with:
    mode: 'full'
    run-security-scan: 'true'
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `python-version` | Python version to install | No | `'3.11'` |
| `mode` | CI mode: `test`, `build`, `quality`, or `full` | No | `'full'` |
| `test-directory` | Directory containing tests | No | `'tests/'` |
| `source-directory` | Directory containing source code | No | `'src/'` |
| `coverage-threshold` | Minimum coverage threshold percentage | No | `'80'` |
| `run-quality-checks` | Enable code quality checks (ruff, mypy) | No | `'true'` |
| `run-security-scan` | Enable security scanning | No | `'false'` |
| `dependency-groups` | Dependency groups to install (for PEP 735) | No | `'dev'` |
| `upload-artifacts` | Upload build artifacts | No | `'true'` |

## Outputs

| Output | Description |
|--------|-------------|
| `python-version` | Installed Python version |
| `coverage-percentage` | Test coverage percentage |
| `build-success` | Whether build was successful |
| `package-version` | Built package version |

## Modes

### `full` (Default)

Runs all steps:
1. Setup Python and UV
2. Install dependencies
3. Code quality checks (ruff, mypy)
4. Security scanning (if enabled)
5. Run tests with coverage
6. Build package
7. Upload artifacts

### `test`

Runs only:
1. Setup Python and UV
2. Install dependencies
3. Run tests with coverage
4. Upload test results

### `build`

Runs only:
1. Setup Python and UV
2. Install dependencies
3. Build package
4. Upload build artifacts

### `quality`

Runs only:
1. Setup Python and UV
2. Install dependencies
3. Code quality checks (ruff, mypy)

### `security`

Runs only:
1. Setup Python and UV
2. Install dependencies
3. Security scanning

## How It Works

### 1. Setup Python

Installs Python and UV package manager.

### 2. Install Dependencies

Supports both PEP 735 dependency groups and legacy optional dependencies:

```bash
# PEP 735 (preferred)
uv pip install --system -e . --group dev

# Legacy optional dependencies
uv pip install --system -e .[dev]
```

### 3. Code Quality Checks

Runs when `run-quality-checks: 'true'` and mode includes quality:

```bash
# Ruff linting
ruff check src/

# Ruff formatting check
ruff format --check src/

# MyPy type checking
mypy src/
```

### 4. Security Scanning

Runs when `run-security-scan: 'true'`:

```bash
# Bandit security scan
bandit -r src/ -f json -o bandit-report.json
```

### 5. Run Tests

Executes PyTest with coverage:

```bash
pytest tests/ \
  --cov=src/ \
  --cov-report=xml \
  --cov-report=term \
  --cov-fail-under=80 \
  --junitxml=test-results.xml
```

Extracts coverage percentage from `coverage.xml`.

### 6. Build Package

Builds wheel and source distribution:

```bash
uv build
```

Extracts package version from built wheel filename.

### 7. Upload Artifacts

Uploads (when `upload-artifacts: 'true'`):
- **python-packages**: Wheel and source distributions (90 days retention)
- **test-results**: JUnit XML, coverage XML, Bandit JSON (30 days retention)

### 8. CI Summary

Generates GitHub step summary with:
- Configuration details
- Test coverage results
- Build results and version
- Artifact upload status

## Examples

### Basic CI

```yaml
jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: provide-io/ci-tooling/actions/python-ci@v0.0.1
```

### With Custom Threshold

```yaml
- uses: provide-io/ci-tooling/actions/python-ci@v0.0.1
  with:
    coverage-threshold: 90
```

### Multiple Python Versions

```yaml
strategy:
  matrix:
    python-version: ['3.11', '3.12', '3.13']

steps:
  - uses: actions/checkout@v4
  - uses: provide-io/ci-tooling/actions/python-ci@v0.0.1
    with:
      python-version: ${{ matrix.python-version }}
```

### Separate Test and Build Jobs

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: provide-io/ci-tooling/actions/python-ci@v0.0.1
        with:
          mode: 'test'

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: provide-io/ci-tooling/actions/python-ci@v0.0.1
        with:
          mode: 'build'
```

### Using Outputs

```yaml
- name: Run CI
  id: ci
  uses: provide-io/ci-tooling/actions/python-ci@v0.0.1

- name: Check Results
  run: |
    echo "Coverage: ${{ steps.ci.outputs.coverage-percentage }}%"
    echo "Build: ${{ steps.ci.outputs.build-success }}"
    echo "Version: ${{ steps.ci.outputs.package-version }}"
```

### With Security Scanning

Requires `security-events: write` permission:

```yaml
permissions:
  contents: read
  security-events: write

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: provide-io/ci-tooling/actions/python-ci@v0.0.1
        with:
          run-security-scan: 'true'
```

## Artifacts

### python-packages

Contains built distributions:
- `*.whl` - Wheel distribution
- `*.tar.gz` - Source distribution

Retention: 90 days

Download in subsequent jobs:

```yaml
- uses: actions/download-artifact@v4
  with:
    name: python-packages
```

### test-results

Contains test outputs:
- `test-results.xml` - JUnit format test results
- `coverage.xml` - Coverage report
- `bandit-report.json` - Security scan results (if enabled)

Retention: 30 days

## Permissions

### Basic CI

```yaml
permissions:
  contents: read
```

### With Security Scanning

```yaml
permissions:
  contents: read
  security-events: write
```

### With Artifact Upload

```yaml
permissions:
  contents: read
  actions: write  # For artifact upload
```

## Troubleshooting

### Coverage Below Threshold

Adjust threshold or improve test coverage:

```yaml
- uses: provide-io/ci-tooling/actions/python-ci@v0.0.1
  with:
    coverage-threshold: 70  # Lower threshold
```

### Quality Checks Failing

Disable temporarily:

```yaml
- uses: provide-io/ci-tooling/actions/python-ci@v0.0.1
  with:
    run-quality-checks: 'false'
```

### Custom Source/Test Directories

```yaml
- uses: provide-io/ci-tooling/actions/python-ci@v0.0.1
  with:
    source-directory: 'lib/'
    test-directory: 'spec/'
```

### Dependencies Not Found

Check `dependency-groups` input:

```yaml
- uses: provide-io/ci-tooling/actions/python-ci@v0.0.1
  with:
    dependency-groups: 'dev,test'
```

## Requirements

- Python 3.11+
- `pyproject.toml` with proper configuration
- Tests in specified test directory
- Source code in specified source directory

## Platform Support

| Platform | Support | Notes |
|----------|---------|-------|
| `ubuntu-latest` | ✅ Full | Recommended |
| `macos-latest` | ✅ Full | |
| `windows-latest` | ✅ Full | |

## Performance

Typical execution times:

| Mode | Time | Notes |
|------|------|-------|
| `test` | 1-2min | Depends on test suite size |
| `build` | 30-60s | Fast with UV |
| `quality` | 30-60s | Depends on codebase size |
| `full` | 2-4min | All steps combined |

## Next Steps

- [setup-python-env](setup-python-env/) - Environment setup details
- [python-release](python-release/) - Release your package
- [Workflows](../workflows/index/) - Complete workflow examples
