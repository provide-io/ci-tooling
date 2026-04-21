# GitHub Actions

Reusable composite actions for Python CI/CD workflows.

## Available Actions

### [setup-python-env](setup-python-env/)

Set up Python, UV package manager, and workenv virtual environment.

**Use this when:** Starting any Python workflow that needs a configured environment.

```yaml
- uses: provide-io/ci-tooling/actions/setup-python-env@v0.0.1
  with:
    python-version: '3.11'
```

**Outputs:** Python version, UV version, workenv path, cache hit status

---

### [python-ci](python-ci/)

Complete CI pipeline with quality checks, testing, security scanning, and building.

**Use this when:** You need a full CI pipeline in one step.

```yaml
- uses: provide-io/ci-tooling/actions/python-ci@v0.0.1
  with:
    mode: 'full'
    coverage-threshold: 80
    run-quality-checks: true
    run-security-scan: true
```

**Outputs:** Python version, coverage percentage, build success, package version

---

### [python-release](python-release/)

Publish packages to PyPI and create GitHub releases.

**Use this when:** Releasing a new version of your package.

```yaml
- uses: provide-io/ci-tooling/actions/python-release@v0.0.1
  with:
    pypi-token: ${{ secrets.PYPI_TOKEN }}
```

**Outputs:** Release version, PyPI URL, GitHub release URL, release result

---

## Action Composition Patterns

### Basic CI Workflow

Use `python-ci` for complete pipeline:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: provide-io/ci-tooling/actions/python-ci@v0.0.1
```

### Custom Workflow

Compose individual actions:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Environment
        uses: provide-io/ci-tooling/actions/setup-python-env@v0.0.1
        with:
          python-version: '3.11'
          install-extras: 'dev,test'

      - name: Run CI
        uses: provide-io/ci-tooling/actions/python-ci@v0.0.1
        with:
          mode: 'test'
          coverage-threshold: 80
```

### Release Workflow

Separate test and release jobs:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: provide-io/ci-tooling/actions/python-ci@v0.0.1
        with:
          mode: 'build'

  release:
    needs: test
    if: startsWith(github.ref, 'refs/tags/v')
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Environment
        uses: provide-io/ci-tooling/actions/setup-python-env@v0.0.1

      - name: Build Package
        uses: provide-io/ci-tooling/actions/python-ci@v0.0.1
        with:
          mode: 'build'

      - name: Publish Release
        uses: provide-io/ci-tooling/actions/python-release@v0.0.1
        with:
          pypi-token: ${{ secrets.PYPI_TOKEN }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

## Common Inputs

Most actions share these common inputs:

| Input | Description | Default |
|-------|-------------|---------|
| `python-version` | Python version to install | `'3.11'` |
| `workenv-path` | Path to virtual environment | `'./workenv'` |
| `source-directory` | Source code directory | `'src/'` |
| `test-directory` | Test directory | `'tests/'` |

## Common Outputs

Most actions provide outputs you can use in subsequent steps:

```yaml
- name: Run CI
  id: ci
  uses: provide-io/ci-tooling/actions/python-ci@v0.0.1

- name: Check Coverage
  run: |
    echo "Coverage: ${{ steps.ci.outputs.coverage-percentage }}%"
    if [ "${{ steps.ci.outputs.coverage-percentage }}" -lt "80" ]; then
      echo "Coverage below threshold!"
      exit 1
    fi
```

## Version Pinning

Always pin to specific versions for stability:

```yaml
# Recommended: Pin to release tag
- uses: provide-io/ci-tooling/actions/python-ci@v0.0.1

# Acceptable: Pin to commit SHA
- uses: provide-io/ci-tooling/actions/python-ci@abc123

# Not recommended: Use main branch (unstable)
- uses: provide-io/ci-tooling/actions/python-ci@main
```

## Permissions

Some actions require specific permissions:

### For `python-ci` with security scanning:

```yaml
permissions:
  contents: read
  security-events: write  # For SARIF upload
```

### For `python-release`:

```yaml
permissions:
  contents: write  # For GitHub releases
  id-token: write  # For PyPI trusted publishing
```

## Caching

Actions use GitHub's caching automatically:

- **UV dependencies** - Cached based on `pyproject.toml` hash
- **Python packages** - Cached in `workenv/`
- **Test results** - Cached for incremental testing

Cache keys are automatically generated based on:

- Operating system
- Python version
- Dependency file hashes

## Matrix Testing

Test across multiple configurations:

```yaml
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

## Artifacts

Actions automatically upload artifacts:

- **Test results** - JUnit XML, coverage reports
- **Security reports** - Bandit JSON, SARIF files
- **Build artifacts** - Wheel and source distributions

Access artifacts in workflow:

```yaml
- uses: actions/download-artifact@v4
  with:
    name: python-packages
```

## Debugging

Enable debug logging:

```yaml
env:
  ACTIONS_STEP_DEBUG: true
  ACTIONS_RUNNER_DEBUG: true

steps:
  - uses: provide-io/ci-tooling/actions/python-ci@v0.0.1
```

## Next Steps

- [setup-python-env](setup-python-env/) - Environment setup reference
- [python-ci](python-ci/) - CI pipeline reference
- [python-release](python-release/) - Release action reference
- [Workflows](../workflows/index/) - Complete workflow examples
