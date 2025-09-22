# Python Build & Release Action

A comprehensive GitHub Action that builds Python packages and conditionally deploys them to TestPyPI and/or PyPI with toggleable options.

## Features

- **Unified Build & Release**: Combines building and deployment in one action
- **Toggleable Deployments**: Choose to deploy to TestPyPI, PyPI, both, or neither
- **Trusted Publishing Support**: Works with modern trusted publishing (no tokens needed)
- **Legacy Token Support**: Falls back to API tokens if needed
- **Dry Run Mode**: Validate builds and configurations without deploying
- **Comprehensive Reporting**: Detailed step summaries with package URLs

## Usage

### Basic Build Only

```yaml
- name: 📦 Build Package
  uses: provide-io/ci-tooling/actions/python-build-release@main
  with:
    deploy-testpypi: false
    deploy-pypi: false
```

### Build and Deploy to TestPyPI

```yaml
- name: 🧪 Build & Deploy to TestPyPI
  uses: provide-io/ci-tooling/actions/python-build-release@main
  with:
    deploy-testpypi: true
    deploy-pypi: false
```

### Build and Deploy to Both TestPyPI and PyPI

```yaml
- name: 🚀 Build & Deploy to Both
  uses: provide-io/ci-tooling/actions/python-build-release@main
  with:
    deploy-testpypi: true
    deploy-pypi: true
```

### Production Release (PyPI Only)

```yaml
- name: 🚀 Production Release
  uses: provide-io/ci-tooling/actions/python-build-release@main
  with:
    deploy-testpypi: false
    deploy-pypi: true
```

### Dry Run Validation

```yaml
- name: 🧪 Validate Release
  uses: provide-io/ci-tooling/actions/python-build-release@main
  with:
    dry-run: true
    deploy-testpypi: true
    deploy-pypi: true
```

## Complete Workflow Examples

### CI Workflow with Optional TestPyPI

```yaml
name: 🧪 CI Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:
    inputs:
      deploy-testpypi:
        description: 'Deploy to TestPyPI'
        type: boolean
        default: false

jobs:
  ci:
    runs-on: ubuntu-latest
    environment: testpypi  # Only needed if using trusted publishing
    permissions:
      id-token: write  # For trusted publishing
      contents: read

    steps:
      - uses: actions/checkout@v4

      - name: 🧪 Run Tests
        uses: provide-io/ci-tooling/actions/python-test@main

      - name: 📦 Build & Release
        uses: provide-io/ci-tooling/actions/python-build-release@main
        with:
          deploy-testpypi: ${{ github.event.inputs.deploy-testpypi || 'false' }}
          deploy-pypi: false
```

### Release Workflow with Both Options

```yaml
name: 🚀 Release

on:
  workflow_dispatch:
    inputs:
      target:
        description: 'Release target'
        required: true
        type: choice
        options:
          - testpypi
          - pypi
          - both
          - dry-run

jobs:
  release:
    runs-on: ubuntu-latest
    environment:
      name: ${{ github.event.inputs.target == 'pypi' || github.event.inputs.target == 'both' ? 'pypi' : 'testpypi' }}
    permissions:
      id-token: write
      contents: read

    steps:
      - uses: actions/checkout@v4

      - name: 🚀 Build & Release
        uses: provide-io/ci-tooling/actions/python-build-release@main
        with:
          dry-run: ${{ github.event.inputs.target == 'dry-run' }}
          deploy-testpypi: ${{ contains(github.event.inputs.target, 'testpypi') || github.event.inputs.target == 'both' }}
          deploy-pypi: ${{ contains(github.event.inputs.target, 'pypi') || github.event.inputs.target == 'both' }}
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `build-backend` | Build backend (uv, build, setuptools) | No | `uv` |
| `python-version` | Python version to use | No | `3.11` |
| `install-extras` | Extra dependencies to install | No | `dev` |
| `workenv-path` | Path to workenv directory | No | `./workenv` |
| `deploy-testpypi` | Deploy to TestPyPI | No | `false` |
| `deploy-pypi` | Deploy to PyPI | No | `false` |
| `skip-existing` | Skip if package exists | No | `true` |
| `verify-metadata` | Verify package metadata | No | `true` |
| `testpypi-token` | TestPyPI API token (legacy) | No | `''` |
| `pypi-token` | PyPI API token (legacy) | No | `''` |
| `dry-run` | Dry run mode | No | `false` |

## Outputs

| Output | Description |
|--------|-------------|
| `build-result` | Build result (success/failed) |
| `package-version` | Package version |
| `wheel-file` | Path to wheel file |
| `sdist-file` | Path to source distribution |
| `testpypi-url` | TestPyPI package URL |
| `pypi-url` | PyPI package URL |
| `deployment-summary` | Summary of deployments |

## Authentication

### Trusted Publishing (Recommended)

Configure trusted publishing on PyPI/TestPyPI:
1. Go to your project settings on PyPI/TestPyPI
2. Add a trusted publisher for your GitHub repository
3. Use appropriate environment protection in your workflow

### Legacy API Tokens

Pass tokens as secrets:
```yaml
with:
  testpypi-token: ${{ secrets.TEST_PYPI_API_TOKEN }}
  pypi-token: ${{ secrets.PYPI_API_TOKEN }}
```

## Common Patterns

### Progressive Deployment

1. **Development**: Build only
2. **Staging**: Build + TestPyPI
3. **Production**: Build + PyPI
4. **Full Release**: Build + Both

### Validation Workflow

Use `dry-run: true` to:
- Validate build configuration
- Check package metadata
- Preview deployment targets
- Test workflow logic

## Environment Setup

The action automatically sets up the Python environment, but you can customize:

```yaml
with:
  python-version: '3.12'
  install-extras: 'dev,test'
  build-backend: 'build'
```