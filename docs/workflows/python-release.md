# python-release.yml

Reusable workflow for automated Python package releases with testing, building, and publishing to PyPI.

## Overview

Complete release pipeline:

1. **Test** - Run full CI test suite
2. **Build** - Build wheel and source distributions
3. **Publish** - Upload to PyPI
4. **Release** - Create GitHub release with artifacts

## Usage

### Basic Release on Tags

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    permissions:
      contents: write
      id-token: write
    uses: provide-io/ci-tooling/.github/workflows/python-release.yml@v0.0.1
    with:
      python-version: '3.11'
    secrets:
      pypi-token: ${{ secrets.PYPI_TOKEN }}
```

### Test PyPI Release

```yaml
jobs:
  release:
    uses: provide-io/ci-tooling/.github/workflows/python-release.yml@v0.0.1
    with:
      python-version: '3.11'
      repository-url: 'https://test.pypi.org/legacy/'
    secrets:
      pypi-token: ${{ secrets.TEST_PYPI_TOKEN }}
```

### Dry Run

```yaml
jobs:
  release:
    uses: provide-io/ci-tooling/.github/workflows/python-release.yml@v0.0.1
    with:
      dry-run: true
    secrets:
      pypi-token: ${{ secrets.PYPI_TOKEN }}
```

## Inputs

| Input | Type | Description | Default |
|-------|------|-------------|---------|
| `python-version` | string | Python version to use | `'3.11'` |
| `uv-version` | string | UV version to use | `'0.7.8'` |
| `test-directory` | string | Test directory | `'tests/'` |
| `coverage-threshold` | number | Coverage threshold | `80` |
| `skip-tests` | boolean | Skip test job | `false` |
| `repository-url` | string | PyPI repository URL | `'https://upload.pypi.org/legacy/'` |
| `skip-existing` | boolean | Skip if package exists | `true` |
| `create-github-release` | boolean | Create GitHub release | `true` |
| `prerelease` | boolean | Mark as prerelease | `false` |
| `dry-run` | boolean | Validate without publishing | `false` |
| `release-notes-file` | string | Path to release notes | `''` |

## Secrets

| Secret | Description | Required |
|--------|-------------|----------|
| `pypi-token` | PyPI API token | Yes (unless trusted publishing) |
| `github-token` | GitHub token | No (auto-provided) |

## Outputs

| Output | Description |
|--------|-------------|
| `release-version` | Released version |
| `pypi-url` | PyPI package URL |
| `github-release-url` | GitHub release URL |

## Jobs

### test

Runs complete test suite before release:

- Code quality checks
- Unit tests with coverage
- Security scanning
- Ensures package is ready for release

### build

Builds package distributions:

- Creates wheel (`.whl`)
- Creates source distribution (`.tar.gz`)
- Validates package metadata
- Uploads artifacts

### publish

Publishes to PyPI:

- Verifies metadata with twine
- Uploads to PyPI (or Test PyPI)
- Skips if package version exists (optional)
- Uses official PyPA publish action

### release

Creates GitHub release:

- Creates Git tag (if not exists)
- Generates release notes
- Attaches build artifacts
- Marks as prerelease (optional)

## Job Dependencies

```
test
 └── build (depends on test)
      └── publish (depends on build)
           └── release (depends on publish)
```

All jobs run sequentially. If any job fails, subsequent jobs are skipped.

## Examples

### Complete Release Workflow

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

permissions:
  contents: write
  id-token: write

jobs:
  release:
    uses: provide-io/ci-tooling/.github/workflows/python-release.yml@v0.0.1
    with:
      python-version: '3.11'
      coverage-threshold: 85
    secrets:
      pypi-token: ${{ secrets.PYPI_TOKEN }}
```

### Manual Release Trigger

```yaml
name: Release

on:
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to release'
        required: true
        type: string

jobs:
  release:
    uses: provide-io/ci-tooling/.github/workflows/python-release.yml@v0.0.1
    with:
      python-version: '3.11'
    secrets:
      pypi-token: ${{ secrets.PYPI_TOKEN }}
```

### Test Then Release

```yaml
name: CI/CD

on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  ci:
    if: "!startsWith(github.ref, 'refs/tags/v')"
    uses: provide-io/ci-tooling/.github/workflows/python-ci.yml@v0.0.1

  release:
    if: startsWith(github.ref, 'refs/tags/v')
    uses: provide-io/ci-tooling/.github/workflows/python-release.yml@v0.0.1
    secrets:
      pypi-token: ${{ secrets.PYPI_TOKEN }}
```

### Prerelease

```yaml
on:
  push:
    tags:
      - 'v*-alpha*'
      - 'v*-beta*'
      - 'v*-rc*'

jobs:
  release:
    uses: provide-io/ci-tooling/.github/workflows/python-release.yml@v0.0.1
    with:
      prerelease: true
    secrets:
      pypi-token: ${{ secrets.PYPI_TOKEN }}
```

### Skip Tests (Not Recommended)

```yaml
jobs:
  release:
    uses: provide-io/ci-tooling/.github/workflows/python-release.yml@v0.0.1
    with:
      skip-tests: true  # Use only if tests ran in previous job
    secrets:
      pypi-token: ${{ secrets.PYPI_TOKEN }}
```

## PyPI Token Setup

### Create PyPI Token

1. Log in to [PyPI](https://pypi.org/)
2. Account Settings → API tokens
3. "Add API token"
4. Name: "GitHub Actions - {repo-name}"
5. Scope: Project or account-wide
6. Copy token (starts with `pypi-`)

### Add to GitHub

1. Repository Settings → Secrets and variables → Actions
2. "New repository secret"
3. Name: `PYPI_TOKEN`
4. Value: Paste PyPI token
5. "Add secret"

### Test PyPI (Optional)

Same steps on [Test PyPI](https://test.pypi.org/):
- Create token
- Add as `TEST_PYPI_TOKEN`
- Use with `repository-url: 'https://test.pypi.org/legacy/'`

## Trusted Publishing (Alternative)

PyPI supports trusted publishing without tokens:

1. Configure on PyPI:
   - Project Settings → Publishing
   - Add trusted publisher
   - Owner: your-org
   - Repository: your-repo
   - Workflow: release.yml
   - Environment: release (optional)

2. Update workflow:
```yaml
permissions:
  id-token: write  # For trusted publishing
  contents: write

jobs:
  release:
    uses: provide-io/ci-tooling/.github/workflows/python-release.yml@v0.0.1
    # No pypi-token needed!
```

## Permissions

### Required

```yaml
permissions:
  contents: write  # For GitHub releases
```

### With Trusted Publishing

```yaml
permissions:
  contents: write
  id-token: write  # For PyPI trusted publishing
```

### Environment Protection

```yaml
jobs:
  release:
    environment: production  # Requires approval
    uses: provide-io/ci-tooling/.github/workflows/python-release.yml@v0.0.1
```

## Release Notes

### Auto-Generated

Default behavior - generates notes with:
- Version number
- PyPI package link
- Artifact list

### Custom File

```yaml
with:
  release-notes-file: 'CHANGELOG.md'
```

Workflow will read and use file content.

### Inline Notes

```yaml
with:
  release-notes: |
    ## What's New
    - Feature A
    - Feature B

    ## Bug Fixes
    - Fix #123
```

## Artifacts

### python-packages

Contains:
- `*.whl` - Wheel distribution
- `*.tar.gz` - Source distribution

Retention: 90 days

Available for download from:
- Workflow run page
- GitHub release page
- PyPI package page

## Troubleshooting

### Package Already Exists

If version already published:

```yaml
with:
  skip-existing: true  # Skip without error
```

Or bump version in `VERSION` file.

### Tests Failing

Fix tests or skip (not recommended):

```yaml
with:
  skip-tests: true
```

### Metadata Validation Failed

Check `pyproject.toml`:
- Valid `readme` field
- Complete `description`
- Valid `license` identifier

Test locally:
```bash
uv build
twine check dist/*
```

### GitHub Release Failed

Ensure:
- Tag exists: `git push --tags`
- Permissions: `contents: write`
- Valid token

### PyPI Upload Failed

Check:
- Valid token
- Token has correct scope
- Version not already published
- Package name available (first release)

## Version Bumping

### Semantic Versioning

Follow [semver.org](https://semver.org/):

```bash
# Patch (1.0.0 → 1.0.1)
echo "1.0.1" > VERSION

# Minor (1.0.1 → 1.1.0)
echo "1.1.0" > VERSION

# Major (1.1.0 → 2.0.0)
echo "2.0.0" > VERSION
```

### Create Tag

```bash
git add VERSION
git commit -m "Bump version to 1.1.0"
git tag v1.1.0
git push && git push --tags
```

### Automated

Use `bump2version`:

```bash
bump2version patch  # Patch version
bump2version minor  # Minor version
bump2version major  # Major version
```

## Dry Run Workflow

Test releases before publishing:

1. **Create dry-run workflow** (`.github/workflows/test-release.yml`):
```yaml
name: Test Release

on:
  pull_request:
    branches: [main]

jobs:
  test-release:
    uses: provide-io/ci-tooling/.github/workflows/python-release.yml@v0.0.1
    with:
      dry-run: true
    secrets:
      pypi-token: ${{ secrets.PYPI_TOKEN }}
```

2. **Verify in PR**: Dry run executes on PRs
3. **Review**: Check step summary for validation results
4. **Merge**: Actual release on tag push

## Release Checklist

Before creating release:

- [ ] Update `VERSION` file
- [ ] Update `CHANGELOG.md` (if used)
- [ ] Update documentation
- [ ] Run tests locally: `pytest`
- [ ] Build locally: `uv build`
- [ ] Validate: `twine check dist/*`
- [ ] Commit changes
- [ ] Create and push tag

## Best Practices

### Always Test Before Release

Don't skip tests. They catch issues before users do.

### Use Semantic Versioning

Follow semver conventions:
- Major: Breaking changes
- Minor: New features
- Patch: Bug fixes

### Write Release Notes

Document what changed:
- New features
- Bug fixes
- Breaking changes
- Upgrade notes

### Test on Test PyPI First

For major releases:
1. Release to Test PyPI
2. Test installation: `pip install --index-url https://test.pypi.org/simple/ package-name`
3. Verify functionality
4. Release to production PyPI

## Security

- **Never commit tokens**: Always use GitHub Secrets
- **Use project-scoped tokens**: Limit token access
- **Enable 2FA**: Require 2FA for PyPI account
- **Rotate tokens regularly**: Every 90 days
- **Consider trusted publishing**: More secure than tokens

## Performance

Typical workflow execution:

| Job | Time | Notes |
|-----|------|-------|
| test | 2-4min | Full CI test suite |
| build | 30-60s | Package building |
| publish | 30-60s | PyPI upload |
| release | 30-60s | GitHub release |
| **Total** | **4-7min** | Complete pipeline |

## Next Steps

- [python-ci.yml](python-ci/) - CI workflow reference
- [Actions](../actions/index/) - Individual actions
- [Quick Start](../getting-started/quick-start/) - Getting started
