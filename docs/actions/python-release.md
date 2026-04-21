# python-release

Publish Python packages to PyPI and create GitHub releases.

## Overview

This composite action automates package releases:

- **PyPI Publishing**: Upload to PyPI using official PyPA action
- **GitHub Releases**: Create releases with artifacts
- **Metadata Verification**: Validate package metadata
- **Dry Run Mode**: Test releases without publishing
- **Release Notes**: Automatic or custom release notes

## Usage

### Basic Release

```yaml
- name: Publish Release
  uses: provide-io/ci-tooling/actions/python-release@v0.0.1
  with:
    pypi-token: ${{ secrets.PYPI_TOKEN }}
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

### Test PyPI

```yaml
- name: Publish to Test PyPI
  uses: provide-io/ci-tooling/actions/python-release@v0.0.1
  with:
    pypi-token: ${{ secrets.TEST_PYPI_TOKEN }}
    repository-url: 'https://test.pypi.org/legacy/'
```

### Dry Run

```yaml
- name: Validate Release
  uses: provide-io/ci-tooling/actions/python-release@v0.0.1
  with:
    pypi-token: ${{ secrets.PYPI_TOKEN }}
    dry-run: 'true'
```

### With Custom Release Notes

```yaml
- name: Publish with Notes
  uses: provide-io/ci-tooling/actions/python-release@v0.0.1
  with:
    pypi-token: ${{ secrets.PYPI_TOKEN }}
    release-notes: |
      ## What's New
      - Feature A
      - Feature B
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `pypi-token` | PyPI API token for publishing | Yes | - |
| `github-token` | GitHub token for creating releases | No | `${{ github.token }}` |
| `repository-url` | PyPI repository URL (for TestPyPI) | No | `'https://upload.pypi.org/legacy/'` |
| `skip-existing` | Skip uploading if package already exists | No | `'true'` |
| `verify-metadata` | Verify package metadata before upload | No | `'true'` |
| `create-github-release` | Create GitHub release | No | `'true'` |
| `release-notes` | Release notes content | No | `''` |
| `release-notes-file` | Path to release notes file | No | `''` |
| `prerelease` | Mark as prerelease | No | `'false'` |
| `workenv-path` | Path to workenv directory | No | `'./workenv'` |
| `artifacts-path` | Path to build artifacts | No | `'dist/'` |
| `dry-run` | Dry run mode - validate without publishing | No | `'false'` |

## Outputs

| Output | Description |
|--------|-------------|
| `release-version` | Released version |
| `pypi-url` | PyPI package URL |
| `github-release-url` | GitHub release URL |
| `release-result` | Release result (`success` or `failed`) |

## How It Works

### 1. Get Release Version

Extracts version from built wheel filename:

```bash
# Example: my_package-1.2.3-py3-none-any.whl
# Extracts: 1.2.3
```

### 2. Verify Package Metadata

When `verify-metadata: 'true'`:

```bash
twine check dist/*
```

Validates:
- Package structure
- Metadata completeness
- README rendering
- Distribution format

### 3. Dry Run (Optional)

When `dry-run: 'true'`:
- Validates packages without uploading
- Shows what would be published
- Checks metadata
- Outputs summary

### 4. Upload to PyPI

Uses official `pypa/gh-action-pypi-publish@release/v1`:
- Secure token-based authentication
- Automatic retry on transient failures
- Skip existing packages (optional)
- Metadata verification

### 5. Generate PyPI URL

Constructs package URL:

```
https://pypi.org/project/{package-name}/{version}/
```

### 6. Prepare Release Notes

Priority order:
1. `release-notes` input (direct content)
2. `release-notes-file` input (file path)
3. Auto-generated (version, PyPI link, artifacts list)

### 7. Create GitHub Release

When `create-github-release: 'true'`:
- Creates Git tag (`v{version}`)
- Creates GitHub release
- Attaches build artifacts
- Includes release notes

### 8. Release Summary

Generates step summary with:
- Release mode (production or dry run)
- Version released
- PyPI URL
- GitHub release URL
- Artifact list
- Next steps (for dry run)

## Examples

### Complete Release Workflow

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      id-token: write

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
```

### Test Before Production Release

```yaml
jobs:
  test-release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: provide-io/ci-tooling/actions/setup-python-env@v0.0.1

      - name: Build
        uses: provide-io/ci-tooling/actions/python-ci@v0.0.1
        with:
          mode: 'build'

      - name: Dry Run
        uses: provide-io/ci-tooling/actions/python-release@v0.0.1
        with:
          pypi-token: ${{ secrets.PYPI_TOKEN }}
          dry-run: 'true'

  production-release:
    needs: test-release
    if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags/v')
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: provide-io/ci-tooling/actions/setup-python-env@v0.0.1

      - name: Build
        uses: provide-io/ci-tooling/actions/python-ci@v0.0.1
        with:
          mode: 'build'

      - name: Publish
        uses: provide-io/ci-tooling/actions/python-release@v0.0.1
        with:
          pypi-token: ${{ secrets.PYPI_TOKEN }}
```

### With Release Notes File

```yaml
- name: Publish with Release Notes
  uses: provide-io/ci-tooling/actions/python-release@v0.0.1
  with:
    pypi-token: ${{ secrets.PYPI_TOKEN }}
    release-notes-file: 'CHANGELOG.md'
```

### Prerelease

```yaml
- name: Publish Prerelease
  uses: provide-io/ci-tooling/actions/python-release@v0.0.1
  with:
    pypi-token: ${{ secrets.PYPI_TOKEN }}
    prerelease: 'true'
```

### Using Outputs

```yaml
- name: Publish Release
  id: release
  uses: provide-io/ci-tooling/actions/python-release@v0.0.1
  with:
    pypi-token: ${{ secrets.PYPI_TOKEN }}

- name: Announce Release
  run: |
    echo "Released version: ${{ steps.release.outputs.release-version }}"
    echo "PyPI: ${{ steps.release.outputs.pypi-url }}"
    echo "GitHub: ${{ steps.release.outputs.github-release-url }}"
```

## PyPI Token Setup

### Create PyPI API Token

1. Log in to [PyPI](https://pypi.org/)
2. Go to Account Settings → API tokens
3. Click "Add API token"
4. Name: "GitHub Actions"
5. Scope: Select project or account-wide
6. Copy token (starts with `pypi-`)

### Add to GitHub Secrets

1. Go to repository Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `PYPI_TOKEN`
4. Value: Paste your PyPI token
5. Click "Add secret"

### Test PyPI Token

For testing releases:

1. Create token on [Test PyPI](https://test.pypi.org/)
2. Add as `TEST_PYPI_TOKEN` secret
3. Use with `repository-url: 'https://test.pypi.org/legacy/'`

## Permissions

### Required Permissions

```yaml
permissions:
  contents: write  # For creating GitHub releases
  id-token: write  # For PyPI trusted publishing (optional)
```

### With Trusted Publishing

PyPI trusted publishing doesn't require API tokens:

```yaml
permissions:
  contents: write
  id-token: write

steps:
  - uses: provide-io/ci-tooling/actions/python-release@v0.0.1
    with:
      # No pypi-token needed with trusted publishing
      github-token: ${{ secrets.GITHUB_TOKEN }}
```

## Troubleshooting

### Package Already Exists

If package version already exists:

```yaml
- uses: provide-io/ci-tooling/actions/python-release@v0.0.1
  with:
    skip-existing: 'true'  # Skip without error
```

Or bump version in `VERSION` file.

### Metadata Validation Failed

Check package metadata:

```bash
# Local validation
twine check dist/*
```

Fix issues in `pyproject.toml`:
- Add `readme` field
- Complete `description`
- Valid `license` identifier

### GitHub Release Failed

Ensure:
- Tag pushed to repository
- `contents: write` permission
- Valid `github-token`

### PyPI Upload Failed

Check:
- Valid PyPI token
- Token has project scope
- Package name available
- Version not already published

## Release Strategy

### Semantic Versioning

Follow [semver.org](https://semver.org/):

- `1.0.0` - Major release
- `1.1.0` - Minor release (new features)
- `1.1.1` - Patch release (bug fixes)
- `1.0.0-alpha.1` - Prerelease

### Version Bumping

Update `VERSION` file:

```bash
# Patch
echo "1.0.1" > VERSION

# Minor
echo "1.1.0" > VERSION

# Major
echo "2.0.0" > VERSION
```

Commit and tag:

```bash
git add VERSION
git commit -m "Bump version to 1.1.0"
git tag v1.1.0
git push && git push --tags
```

### Automated Versioning

Use a tool like `bump2version`:

```bash
bump2version patch  # 1.0.0 → 1.0.1
bump2version minor  # 1.0.1 → 1.1.0
bump2version major  # 1.1.0 → 2.0.0
```

## Requirements

- Built package artifacts in `dist/`
- Valid `pyproject.toml` metadata
- PyPI account and API token
- Git repository with tags

## Platform Support

| Platform | Support | Notes |
|----------|---------|-------|
| `ubuntu-latest` | ✅ Full | Recommended |
| `macos-latest` | ✅ Full | |
| `windows-latest` | ✅ Full | |

## Security

- **Never commit tokens**: Always use GitHub Secrets
- **Use project-scoped tokens**: Limit token scope to specific projects
- **Enable 2FA**: Require 2FA for PyPI account
- **Rotate tokens**: Regularly rotate API tokens
- **Use trusted publishing**: Consider PyPI trusted publishing

## Next Steps

- [setup-python-env](setup-python-env/) - Environment setup
- [python-ci](python-ci/) - Build packages before release
- [Workflows](../workflows/index/) - Complete release workflow examples
