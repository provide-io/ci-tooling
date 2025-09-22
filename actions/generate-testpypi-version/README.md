# Generate TestPyPI Version Action

A GitHub Action that intelligently generates versions for TestPyPI deployment. Uses base version for first deployment, then switches to post-releases for subsequent deployments of the same version.

## Features

- **Smart Version Detection**: Checks if base version exists on TestPyPI
- **Clean Base Deployments**: First deployment uses clean base version (e.g., `1.2.3`)
- **Continuous Post-Releases**: Subsequent deployments use post-releases (e.g., `1.2.3.post20240921231520`)
- **PEP 440 Compliant**: Generates valid post-release versions
- **Configurable**: Customize package name, version file path, and timestamp format
- **Automatic File Updates**: Optionally updates version file for build process

## Usage

### Basic Usage

```yaml
- name: 🔖 Generate TestPyPI Version
  uses: provide-io/ci-tooling/actions/generate-testpypi-version@main
  id: version
  with:
    package-name: 'my-package'

- name: Use the version
  run: |
    echo "Base version: ${{ steps.version.outputs.base-version }}"
    echo "Deploy version: ${{ steps.version.outputs.deploy-version }}"
    echo "Is post-release: ${{ steps.version.outputs.is-post-release }}"
```

### Advanced Usage

```yaml
- name: 🔖 Generate TestPyPI Version
  uses: provide-io/ci-tooling/actions/generate-testpypi-version@main
  id: version
  with:
    package-name: 'my-package'
    version-file: 'src/mypackage/__version__.py'
    update-file: false
    timestamp-format: '%Y%m%d%H%M%S'
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `package-name` | Name of the package on TestPyPI | Yes | - |
| `version-file` | Path to the version file | No | `VERSION` |
| `update-file` | Whether to update the version file | No | `true` |
| `timestamp-format` | Timestamp format (strftime) | No | `%Y%m%d%H%M%S` |

## Outputs

| Output | Description | Example |
|--------|-------------|---------|
| `base-version` | Original version from file | `1.2.3` |
| `deploy-version` | Version to deploy | `1.2.3` or `1.2.3.post20240921231520` |
| `timestamp` | Timestamp used (if post-release) | `20240921231520` or `none` |
| `is-post-release` | Whether post-release was generated | `true` or `false` |

## How It Works

1. **Read Base Version**: Reads version from the specified file
2. **Check TestPyPI**: Makes HTTP request to `https://test.pypi.org/pypi/{package}/{version}/json`
3. **Decision Logic**:
   - **404 Not Found**: Version doesn't exist → use base version
   - **200 OK**: Version exists → generate post-release with timestamp
4. **Update File**: Optionally updates version file with deploy version
5. **Set Outputs**: Provides all version information for downstream steps

## Use Cases

### TestPyPI Continuous Deployment

Perfect for deploying every commit to TestPyPI with clean versioning:

```yaml
jobs:
  deploy-testpypi:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: 🔖 Generate TestPyPI Version
        uses: provide-io/ci-tooling/actions/generate-testpypi-version@main
        id: version
        with:
          package-name: 'pyvider-cty'

      - name: 📦 Build Package
        run: uv build

      - name: 📤 Deploy to TestPyPI
        run: |
          uv publish --publish-url https://test.pypi.org/legacy/ \
            --token ${{ secrets.TESTPYPI_API_TOKEN }} dist/*
```

### Branch-based Development

Use different logic for different branches:

```yaml
- name: 🔖 Generate Version
  uses: provide-io/ci-tooling/actions/generate-testpypi-version@main
  id: version
  with:
    package-name: 'my-package'
    update-file: ${{ github.ref == 'refs/heads/main' }}

- name: Deploy if main branch
  if: github.ref == 'refs/heads/main'
  run: |
    echo "Deploying ${{ steps.version.outputs.deploy-version }}"
```

## Version Flow Example

| Deployment | Base Version | TestPyPI Status | Deploy Version | Type |
|------------|--------------|-----------------|----------------|------|
| 1st | `1.2.3` | Not found | `1.2.3` | Base |
| 2nd | `1.2.3` | Exists | `1.2.3.post20240921120000` | Post-release |
| 3rd | `1.2.3` | Exists | `1.2.3.post20240921150000` | Post-release |
| 4th | `1.2.4` | Not found | `1.2.4` | Base |

## Error Handling

- **Missing version file**: Action fails with clear error message
- **Network errors**: Treated as version not found (uses base version)
- **Invalid package name**: Will result in 404 (uses base version)

## Best Practices

1. **Use with TestPyPI only**: This action is designed for TestPyPI continuous deployment
2. **Keep base versions clean**: Let the action handle post-release generation
3. **Monitor outputs**: Use `is-post-release` output to conditionally run steps
4. **Version file management**: Consider whether to update the file based on your workflow