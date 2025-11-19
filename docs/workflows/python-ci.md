# python-ci.yml

Reusable workflow for Python continuous integration with quality checks, testing, security scanning, and building.

## Overview

Complete CI pipeline with orchestrated jobs:

1. **Quality** - Code quality checks (ruff, mypy)
2. **Test** - PyTest execution with coverage
3. **Security** - Security scanning (optional)
4. **Performance** - Performance benchmarks (optional)

## Usage

### Basic CI

```yaml
name: CI

on: [push, pull_request]

jobs:
  ci:
    uses: provide-io/ci-tooling/.github/workflows/python-ci.yml@v0.0.1
    with:
      python-version: '3.11'
```

### With Security Scanning

```yaml
jobs:
  ci:
    permissions:
      contents: read
      security-events: write
    uses: provide-io/ci-tooling/.github/workflows/python-ci.yml@v0.0.1
    with:
      python-version: '3.11'
      run-security: true
```

### Matrix Testing

```yaml
jobs:
  ci:
    uses: provide-io/ci-tooling/.github/workflows/python-ci.yml@v0.0.1
    with:
      matrix-testing: true
      os-matrix: 'ubuntu-latest,macos-latest,windows-latest'
```

## Inputs

| Input | Type | Description | Default |
|-------|------|-------------|---------|
| `python-version` | string | Python version to use | `'3.11'` |
| `uv-version` | string | UV version to use | `'0.7.8'` |
| `source-paths` | string | Source paths for quality checks | `'src/ tests/'` |
| `test-directory` | string | Test directory | `'tests/'` |
| `coverage-threshold` | number | Coverage threshold percentage | `80` |
| `run-security` | boolean | Run security scanning | `true` |
| `run-performance` | boolean | Run performance tests | `false` |
| `matrix-testing` | boolean | Enable matrix testing across Python versions | `false` |
| `os-matrix` | string | Operating systems to test on (comma-separated) | `'ubuntu-latest'` |
| `fail-fast` | boolean | Fail fast in matrix builds | `false` |

## Secrets

| Secret | Description | Required |
|--------|-------------|----------|
| `CODECOV_TOKEN` | Codecov token for coverage upload | No |

## Outputs

| Output | Description |
|--------|-------------|
| `coverage-percentage` | Test coverage percentage |
| `package-version` | Built package version |

## Jobs

### quality

Runs first, performs code quality checks:

- **Ruff linting**: `ruff check`
- **Ruff formatting**: `ruff format --check`
- **MyPy type checking**: `mypy src/`

Subsequent jobs only run if quality passes.

### test

Runs after quality, executes tests:

- **PyTest**: Runs test suite
- **Coverage**: Tracks code coverage
- **Matrix**: Optional multi-version/OS testing
- **Artifacts**: Uploads test results and coverage

### security (Optional)

Runs parallel to tests when `run-security: true`:

- **Bandit**: Security vulnerability scanning
- **Safety**: Dependency vulnerability check
- **SARIF**: Upload to GitHub Security tab

### performance (Optional)

Runs when `run-performance: true`:

- **Benchmarks**: Performance benchmark execution
- **Comparison**: Compare against baseline
- **Reports**: Upload benchmark results

## Job Dependencies

```
quality
   ├── test (depends on quality)
   ├── security (parallel to test)
   └── performance (parallel to test)
```

Quality checks must pass before other jobs run. Test, security, and performance jobs run in parallel.

## Examples

### Complete CI Pipeline

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

permissions:
  contents: read
  security-events: write
  pull-requests: write

jobs:
  ci:
    uses: provide-io/ci-tooling/.github/workflows/python-ci.yml@v0.0.1
    with:
      python-version: '3.11'
      coverage-threshold: 85
      run-security: true
      run-performance: false
    secrets:
      codecov-token: ${{ secrets.CODECOV_TOKEN }}
```

### Matrix Testing Example

```yaml
jobs:
  ci:
    uses: provide-io/ci-tooling/.github/workflows/python-ci.yml@v0.0.1
    with:
      matrix-testing: true
      python-version: '3.11'  # Base version, matrix adds 3.12, 3.13
      os-matrix: 'ubuntu-latest,macos-latest'
      fail-fast: false  # Continue testing all combinations
```

### Custom Paths

```yaml
jobs:
  ci:
    uses: provide-io/ci-tooling/.github/workflows/python-ci.yml@v0.0.1
    with:
      source-paths: 'lib/ tests/'
      test-directory: 'spec/'
```

### Using Outputs

```yaml
jobs:
  ci:
    uses: provide-io/ci-tooling/.github/workflows/python-ci.yml@v0.0.1
    with:
      python-version: '3.11'

  deploy:
    needs: ci
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy
        run: |
          echo "Coverage: ${{ needs.ci.outputs.coverage-percentage }}%"
          echo "Deploying version: ${{ needs.ci.outputs.package-version }}"
```

## Matrix Testing

When `matrix-testing: true`, tests run across:

- **Python versions**: 3.11, 3.12, 3.13
- **Operating systems**: As specified in `os-matrix`

Total combinations: `len(python_versions) × len(os_matrix)`

Example with `os-matrix: 'ubuntu-latest,macos-latest'`:
- 3.11 on ubuntu-latest
- 3.11 on macos-latest
- 3.12 on ubuntu-latest
- 3.12 on macos-latest
- 3.13 on ubuntu-latest
- 3.13 on macos-latest

## Permissions

### Minimal (No Security)

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

### With PR Comments

```yaml
permissions:
  contents: read
  pull-requests: write
```

## Artifacts

Automatically uploaded artifacts:

### test-results

- `test-results.xml` - JUnit format
- `coverage.xml` - Coverage report
- Retention: 30 days

### security-results (if enabled)

- `bandit-report.json` - Bandit scan
- `safety-report.json` - Safety check
- `results.sarif` - SARIF format
- Retention: 90 days

### performance-results (if enabled)

- `benchmark-results.json`
- Retention: 30 days

## Codecov Integration

When `CODECOV_TOKEN` secret is provided:

- Coverage reports uploaded to Codecov
- PR comments with coverage delta
- Coverage trends and graphs

Setup:
1. Sign up at [codecov.io](https://codecov.io/)
2. Add repository
3. Copy token
4. Add as `CODECOV_TOKEN` secret

## Troubleshooting

### Quality Checks Failing

Quality job blocks all other jobs. Fix issues or adjust settings:

```yaml
with:
  source-paths: 'src/'  # Exclude tests from quality checks
```

### Coverage Below Threshold

Lower threshold temporarily:

```yaml
with:
  coverage-threshold: 70
```

Or improve test coverage.

### Matrix Jobs Failing

Use `fail-fast: false` to see all failures:

```yaml
with:
  matrix-testing: true
  fail-fast: false
```

### Security Job Blocking

Disable temporarily:

```yaml
with:
  run-security: false
```

## Performance

| Configuration | Time | Notes |
|---------------|------|-------|
| Basic (no matrix) | 2-4min | Single OS, single Python |
| Matrix (3 versions) | 3-6min | Parallel execution |
| Matrix (3 versions, 3 OS) | 4-8min | 9 parallel jobs |
| With security | +1-2min | Parallel to tests |

## Best Practices

### Always Run Quality First

Quality checks are fast and catch common issues early.

### Use Matrix Sparingly

Matrix testing is thorough but resource-intensive. Consider:
- Run on main branch only
- Run on schedule (nightly)
- Run on release PRs only

### Set Appropriate Thresholds

- Start with 70% coverage
- Gradually increase to 80-90%
- Don't aim for 100% immediately

### Enable Security Scanning

Security scans are valuable:
- Catch vulnerabilities early
- Low overhead (parallel to tests)
- Integrates with GitHub Security

## Migration from Custom Workflows

Before:
```yaml
jobs:
  lint:
    steps:
      - run: ruff check src/
  test:
    steps:
      - run: pytest
  build:
    steps:
      - run: uv build
```

After:
```yaml
jobs:
  ci:
    uses: provide-io/ci-tooling/.github/workflows/python-ci.yml@v0.0.1
```

## Next Steps

- [python-release.yml](python-release/) - Release workflow
- [Actions](../actions/index/) - Individual actions
- [Quick Start](../getting-started/quick-start/) - Getting started guide
