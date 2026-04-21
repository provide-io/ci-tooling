# Reusable Workflows

Complete end-to-end CI/CD workflows that can be called from your repository.

## Overview

Reusable workflows provide complete CI/CD pipelines with multiple jobs orchestrated together. They offer:

- **Complete Pipelines**: Quality checks, testing, security, and building
- **Matrix Testing**: Test across multiple Python versions and operating systems
- **Parallel Execution**: Jobs run in parallel for faster results
- **Flexible Configuration**: Extensive input parameters for customization

## Available Workflows

### [python-ci.yml](python-ci/)

Complete CI pipeline with quality, test, security, and performance jobs.

**Use this for:** Continuous integration on push and pull requests.

```yaml
jobs:
  ci:
    uses: provide-io/ci-tooling/.github/workflows/python-ci.yml@v0.0.1
    with:
      python-version: '3.11'
```

---

### [python-release.yml](python-release/)

Complete release pipeline with testing, building, and PyPI publishing.

**Use this for:** Automated releases on version tags.

```yaml
jobs:
  release:
    uses: provide-io/ci-tooling/.github/workflows/python-release.yml@v0.0.1
    with:
      python-version: '3.11'
    secrets:
      pypi-token: ${{ secrets.PYPI_TOKEN }}
```

---

## Workflows vs Actions

### When to Use Workflows

**Reusable workflows** are best when you need:
- Complete multi-job pipelines
- Job orchestration and dependencies
- Matrix testing across configurations
- Standardized CI/CD process
- Minimal configuration

### When to Use Actions

**Individual actions** are best when you need:
- Custom workflow structure
- Fine-grained control over steps
- Integration with other actions
- Custom job dependencies
- Unique workflow requirements

## Calling Reusable Workflows

### Basic Syntax

```yaml
jobs:
  job-name:
    uses: provide-io/ci-tooling/.github/workflows/workflow-name.yml@version
    with:
      input-name: value
    secrets:
      secret-name: ${{ secrets.SECRET_NAME }}
```

### Version Pinning

```yaml
# Recommended: Use release tag
uses: provide-io/ci-tooling/.github/workflows/python-ci.yml@v0.0.1

# Acceptable: Use commit SHA
uses: provide-io/ci-tooling/.github/workflows/python-ci.yml@abc123def

# Not recommended: Use branch (unstable)
uses: provide-io/ci-tooling/.github/workflows/python-ci.yml@main
```

## Common Patterns

### CI on Push and PR

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

### Release on Tags

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    uses: provide-io/ci-tooling/.github/workflows/python-release.yml@v0.0.1
    with:
      python-version: '3.11'
    secrets:
      pypi-token: ${{ secrets.PYPI_TOKEN }}
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

### Separate CI and Release

```yaml
name: CI/CD

on:
  push:
    branches: [main]
    tags: ['v*']
  pull_request:

jobs:
  ci:
    uses: provide-io/ci-tooling/.github/workflows/python-ci.yml@v0.0.1
    with:
      python-version: '3.11'

  release:
    if: startsWith(github.ref, 'refs/tags/v')
    needs: ci
    uses: provide-io/ci-tooling/.github/workflows/python-release.yml@v0.0.1
    secrets:
      pypi-token: ${{ secrets.PYPI_TOKEN }}
```

## Workflow Permissions

### Minimal Permissions (CI)

```yaml
permissions:
  contents: read
  pull-requests: write  # For PR comments

jobs:
  ci:
    uses: provide-io/ci-tooling/.github/workflows/python-ci.yml@v0.0.1
```

### Release Permissions

```yaml
permissions:
  contents: write  # For GitHub releases
  id-token: write  # For PyPI trusted publishing

jobs:
  release:
    uses: provide-io/ci-tooling/.github/workflows/python-release.yml@v0.0.1
```

### Security Scanning Permissions

```yaml
permissions:
  contents: read
  security-events: write  # For SARIF upload

jobs:
  ci:
    uses: provide-io/ci-tooling/.github/workflows/python-ci.yml@v0.0.1
    with:
      run-security: true
```

## Workflow Outputs

Reusable workflows can provide outputs:

```yaml
jobs:
  ci:
    uses: provide-io/ci-tooling/.github/workflows/python-ci.yml@v0.0.1
    with:
      python-version: '3.11'

  deploy:
    needs: ci
    runs-on: ubuntu-latest
    steps:
      - name: Deploy
        run: |
          echo "Coverage: ${{ needs.ci.outputs.coverage-percentage }}"
          echo "Version: ${{ needs.ci.outputs.package-version }}"
```

## Secrets Management

### Required Secrets

For release workflows:

```yaml
secrets:
  pypi-token: ${{ secrets.PYPI_TOKEN }}
  github-token: ${{ secrets.GITHUB_TOKEN }}  # Auto-provided
```

For optional integrations:

```yaml
secrets:
  codecov-token: ${{ secrets.CODECOV_TOKEN }}
```

### Setting Secrets

1. Go to repository Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add secret name and value
4. Reference in workflow with `${{ secrets.SECRET_NAME }}`

## Debugging Workflows

### Enable Debug Logging

```yaml
jobs:
  ci:
    uses: provide-io/ci-tooling/.github/workflows/python-ci.yml@v0.0.1
    with:
      python-version: '3.11'

env:
  ACTIONS_STEP_DEBUG: true
  ACTIONS_RUNNER_DEBUG: true
```

### Check Workflow Logs

1. Go to Actions tab in GitHub
2. Click on workflow run
3. Expand job and step logs
4. Look for errors or warnings

## Workflow Artifacts

Workflows automatically upload:

- Test results (JUnit XML)
- Coverage reports (XML)
- Security scan results (SARIF, JSON)
- Built packages (wheel, sdist)

Download from workflow run page or using:

```yaml
- uses: actions/download-artifact@v4
  with:
    name: artifact-name
```

## Performance Optimization

### Cache Strategy

Workflows use caching automatically:
- UV cache (~/.cache/uv)
- Python packages (workenv/)
- Dependency manifests (pyproject.toml hash)

### Parallel Jobs

Workflows run jobs in parallel:
- Quality checks run first
- Tests run after quality passes
- Security scans run parallel to tests
- Performance tests run parallel (optional)

### Matrix Optimization

```yaml
jobs:
  ci:
    uses: provide-io/ci-tooling/.github/workflows/python-ci.yml@v0.0.1
    with:
      matrix-testing: true
      fail-fast: true  # Stop on first failure
      os-matrix: 'ubuntu-latest'  # Single OS for faster runs
```

## Customization Examples

### Custom Coverage Threshold

```yaml
jobs:
  ci:
    uses: provide-io/ci-tooling/.github/workflows/python-ci.yml@v0.0.1
    with:
      coverage-threshold: 90
```

### Disable Security Scanning

```yaml
jobs:
  ci:
    uses: provide-io/ci-tooling/.github/workflows/python-ci.yml@v0.0.1
    with:
      run-security: false
```

### Custom Source Paths

```yaml
jobs:
  ci:
    uses: provide-io/ci-tooling/.github/workflows/python-ci.yml@v0.0.1
    with:
      source-paths: 'lib/ tests/'
      test-directory: 'spec/'
```

## Troubleshooting

### Workflow Not Triggering

Check:
- Workflow file location (`.github/workflows/`)
- Trigger conditions (`on:` section)
- Branch protection rules
- Repository permissions

### Workflow Failing

Common issues:
- Missing secrets
- Insufficient permissions
- Coverage threshold too high
- Test failures
- Build errors

### Secrets Not Available

Ensure:
- Secrets are set in repository settings
- Secret names match exactly
- Secrets are passed in `secrets:` section
- Caller has access to secrets

## Migration Guide

### From Makefile to Workflows

Before (Makefile):
```makefile
test:
    pytest tests/

quality:
    ruff check src/
    mypy src/
```

After (Workflow):
```yaml
jobs:
  ci:
    uses: provide-io/ci-tooling/.github/workflows/python-ci.yml@v0.0.1
```

### From Custom Workflows

Before (Custom):
```yaml
jobs:
  test:
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -e .[dev]
      - run: pytest
```

After (Reusable):
```yaml
jobs:
  ci:
    uses: provide-io/ci-tooling/.github/workflows/python-ci.yml@v0.0.1
```

## Next Steps

- [python-ci.yml](python-ci/) - CI workflow reference
- [python-release.yml](python-release/) - Release workflow reference
- [Actions](../actions/index/) - Individual action documentation
- [Quick Start](../getting-started/quick-start/) - Get started quickly
