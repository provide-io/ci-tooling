# setup-python-env

Set up Python, UV package manager, and workenv virtual environment for provide.io projects.

## Overview

This composite action configures a complete Python development environment:

- Installs specified Python version
- Installs UV package manager
- Creates `workenv/` virtual environment (not `.venv`)
- Caches dependencies for faster builds
- Installs project dependencies

## Usage

### Basic Usage

```yaml
- name: Setup Python Environment
  uses: provide-io/ci-tooling/actions/setup-python-env@v0.0.1
  with:
    python-version: '3.11'
```

### With Extras

```yaml
- name: Setup Python Environment
  uses: provide-io/ci-tooling/actions/setup-python-env@v0.0.1
  with:
    python-version: '3.11'
    install-extras: 'dev,test,docs'
```

### Custom Workenv Path

```yaml
- name: Setup Python Environment
  uses: provide-io/ci-tooling/actions/setup-python-env@v0.0.1
  with:
    workenv-path: './custom-workenv'
```

### Disable Caching

```yaml
- name: Setup Python Environment
  uses: provide-io/ci-tooling/actions/setup-python-env@v0.0.1
  with:
    cache-dependencies: 'false'
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `python-version` | Python version to install | No | `'3.11'` |
| `uv-version` | UV package manager version | No | `'0.7.8'` |
| `workenv-path` | Path to create workenv directory | No | `'./workenv'` |
| `cache-dependencies` | Enable dependency caching | No | `'true'` |
| `install-extras` | Package extras to install (comma-separated) | No | `'dev'` |
| `project-path` | Path to project root (for editable install) | No | `'.'` |

## Outputs

| Output | Description |
|--------|-------------|
| `python-version` | Installed Python version |
| `uv-version` | Installed UV version |
| `workenv-path` | Path to workenv directory |
| `cache-hit` | Whether dependency cache was hit |

## How It Works

### 1. Setup Python

Uses `actions/setup-python@v5` to install the specified Python version.

### 2. Install UV

Uses `astral-sh/setup-uv@v4` to install UV package manager with caching enabled.

### 3. Create Workenv

Creates a virtual environment at the specified path:

```bash
uv venv ./workenv
```

Adds `workenv/bin` to `$GITHUB_PATH` for subsequent steps.

### 4. Cache Dependencies

Caches:
- `~/.cache/uv` - UV cache directory
- `workenv/` - Virtual environment

Cache key based on:
- Operating system
- Python version
- `pyproject.toml` and `requirements*.txt` hashes

### 5. Install Dependencies

Installs project in editable mode:

```bash
# With extras
uv pip install -e ".[dev,test]"

# Without extras
uv pip install -e .

# Or from requirements.txt if no pyproject.toml
uv pip install -r requirements.txt
```

### 6. Verify Installation

Outputs summary to GitHub step summary:
- Python version
- UV version
- Workenv path
- Number of installed packages

## Examples

### Matrix Testing

```yaml
strategy:
  matrix:
    python-version: ['3.11', '3.12', '3.13']

steps:
  - uses: actions/checkout@v4
  - uses: provide-io/ci-tooling/actions/setup-python-env@v0.0.1
    with:
      python-version: ${{ matrix.python-version }}
```

### Multiple Jobs

```yaml
jobs:
  setup:
    runs-on: ubuntu-latest
    outputs:
      python-version: ${{ steps.setup.outputs.python-version }}
    steps:
      - uses: actions/checkout@v4
      - id: setup
        uses: provide-io/ci-tooling/actions/setup-python-env@v0.0.1

  test:
    needs: setup
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: provide-io/ci-tooling/actions/setup-python-env@v0.0.1
        with:
          python-version: ${{ needs.setup.outputs.python-version }}
```

### With Subsequent Steps

```yaml
- name: Setup Environment
  id: setup
  uses: provide-io/ci-tooling/actions/setup-python-env@v0.0.1

- name: Run Tests
  run: |
    source ${{ steps.setup.outputs.workenv-path }}/bin/activate
    pytest tests/
```

## Cache Behavior

### Cache Hit

When cache is hit:
- ✅ Dependencies restored from cache
- ✅ Faster workflow execution
- ✅ Reduced bandwidth usage

### Cache Miss

When cache misses:
- Downloads and installs all dependencies
- Creates new cache entry
- Subsequent runs will be faster

### Cache Invalidation

Cache is invalidated when:
- `pyproject.toml` changes
- `requirements*.txt` changes
- Python version changes
- Operating system changes

## Troubleshooting

### workenv/ Not Found in Subsequent Steps

Ensure you're using the output path:

```yaml
- id: setup
  uses: provide-io/ci-tooling/actions/setup-python-env@v0.0.1

- run: source ${{ steps.setup.outputs.workenv-path }}/bin/activate
```

### Dependencies Not Installing

Check that your project has either:
- `pyproject.toml` with proper package configuration
- `requirements.txt` file

### Cache Not Working

Verify:
- `cache-dependencies: 'true'` is set
- Repository has caching enabled
- Cache key hasn't exceeded GitHub's 10GB limit

### UV Version Issues

Pin to specific UV version if needed:

```yaml
- uses: provide-io/ci-tooling/actions/setup-python-env@v0.0.1
  with:
    uv-version: '0.7.8'
```

## Requirements

- GitHub Actions runner with bash shell
- Internet access for downloading Python and UV
- Read permissions for repository

## Platform Support

| Platform | Support | Notes |
|----------|---------|-------|
| `ubuntu-latest` | ✅ Full | Recommended |
| `macos-latest` | ✅ Full | |
| `windows-latest` | ✅ Full | Uses PowerShell |

## Performance

Typical execution times:

| Scenario | Time | Notes |
|----------|------|-------|
| Cache hit | 10-20s | Dependencies restored from cache |
| Cache miss | 1-3min | Full dependency installation |
| First run | 1-3min | No cache available |

## Next Steps

- [python-ci](python-ci/) - Use this environment for CI pipeline
- [python-release](python-release/) - Use this environment for releases
- [Workflows](../workflows/index/) - Complete workflow examples
