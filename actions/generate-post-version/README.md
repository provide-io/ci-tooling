# Generate Post Version Action

A GitHub Action that generates post-release versions for continuous deployment to TestPyPI. Post-release versions follow PEP 440 and are treated as normal releases (not pre-releases), making them compatible with `>=X.Y.Z` version requirements.

## Features

- **PEP 440 Compliant**: Generates valid post-release versions like `1.2.3.post20240921231520`
- **Not Pre-releases**: Post-releases satisfy `>=X.Y.Z` requirements without special flags
- **Unique Timestamps**: Each run generates a unique version for continuous deployment
- **Configurable**: Customize version file path and timestamp format
- **Clean**: Optionally update version file temporarily for build process

## Usage

### Basic Usage

```yaml
- name: 🔖 Generate Post Version
  uses: provide-io/ci-tooling/actions/generate-post-version@main
  id: post-version

- name: Use the versions
  run: |
    echo "Base version: ${{ steps.post-version.outputs.base-version }}"
    echo "Post version: ${{ steps.post-version.outputs.post-version }}"
```

### Advanced Usage

```yaml
- name: 🔖 Generate Post Version
  uses: provide-io/ci-tooling/actions/generate-post-version@main
  id: post-version
  with:
    version-file: 'src/mypackage/__version__.py'
    update-file: false
    timestamp-format: '%Y%m%d%H%M%S'
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `version-file` | Path to the version file | No | `VERSION` |
| `update-file` | Whether to update the version file | No | `true` |
| `timestamp-format` | Timestamp format (strftime) | No | `%Y%m%d%H%M%S` |

## Outputs

| Output | Description | Example |
|--------|-------------|---------|
| `base-version` | Original version from file | `0.0.113` |
| `post-version` | Generated post-release version | `0.0.113.post20240921231520` |
| `timestamp` | Timestamp used | `20240921231520` |

## Use Cases

### TestPyPI Continuous Deployment

Perfect for deploying to TestPyPI on every commit:

```yaml
jobs:
  deploy-testpypi:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: 🔖 Generate Post Version
        uses: provide-io/ci-tooling/actions/generate-post-version@main
        id: post-version

      - name: 📦 Build Package
        run: uv build

      - name: 📤 Deploy to TestPyPI
        run: |
          uv publish --publish-url https://test.pypi.org/legacy/ \
            --token ${{ secrets.TESTPYPI_API_TOKEN }} dist/*
```

### Development Builds

For creating development builds without affecting the main version:

```yaml
- name: 🔖 Generate Post Version
  uses: provide-io/ci-tooling/actions/generate-post-version@main
  with:
    update-file: false  # Don't modify the version file
  id: dev-version

- name: Build with dev version
  run: |
    echo "Building version: ${{ steps.dev-version.outputs.post-version }}"
```

## Why Post-Releases?

According to PEP 440:
- **Post-releases are NOT pre-releases**
- They satisfy version specifiers like `>=1.0.0`
- Perfect for patches and continuous deployment
- Compatible with all Python packaging tools (pip, uv, etc.)

## Version Examples

| Base Version | Generated Post Version |
|--------------|----------------------|
| `1.0.0` | `1.0.0.post20240921231520` |
| `0.1.0` | `0.1.0.post20240921231520` |
| `2.3.4` | `2.3.4.post20240921231520` |