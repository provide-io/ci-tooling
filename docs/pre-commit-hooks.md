# Pre-commit Hooks for provide.io Ecosystem

**Zero-friction code conformance through automated pre-commit hooks**

## Overview

The `ci-tooling` repository provides centralized pre-commit hooks that enforce code standards across all provide.io repositories. These hooks automatically:

✅ Add SPDX headers to Python files
✅ Apply repository-specific emoji footers (auto-detected!)
✅ Validate ruff/mypy/pytest configurations
✅ Format code with ruff
✅ Type-check with mypy
✅ Catch common issues before CI

**Key Benefit:** Developers never need to manually run conform scripts or remember footer patterns. Everything happens automatically on `git commit`.

---

## Quick Start

### For New Repos

```bash
cd your-repo
make setup-pre-commit  # Installs pre-commit hooks
git add .
git commit             # Hooks run automatically!
```

### For Existing Developers

```bash
# One-time setup
pip install pre-commit

# In each repo
cd pyvider
make setup-pre-commit
```

That's it! Hooks now run automatically on every commit.

---

## Available Hooks

### 1. `provide-conform` - SPDX Headers & Footers

**What it does:**
- Automatically adds SPDX copyright and license headers
- Detects repository from git remote (no `--footer` flag needed!)
- Applies correct emoji footer from central registry
- Preserves module docstrings
- Strips old footers before adding new ones

**Example:**
```python
# Before commit (missing headers)
def my_function():
    pass

# After commit (auto-fixed)
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""TODO: Add module docstring."""

def my_function():
    pass

# 🐍🔌🔚
```

**Repository Detection:**
- Reads git remote URL (e.g., `github.com/provide-io/pyvider.git`)
- Extracts repo name (`pyvider`)
- Looks up footer in central registry
- Applies correct footer automatically

**Footer Registry:**
The central registry is maintained in `ci-tooling/src/provide/cicd/footer_registry.json`:

```json
{
  "repositories": {
    "pyvider": "# 🐍🔌🔚",
    "flavorpack": "# 🌶️📦🔚",
    "provide-testkit": "# 🧪✅🔚",
    ...
  }
}
```

### 2. `provide-config-check` - Configuration Validation

**What it does:**
- Validates `pyproject.toml` matches canonical standards
- Checks ruff configuration (line-length, rules, format)
- Checks mypy configuration (strict mode, options)
- Checks pytest configuration (markers, paths)
- Reports errors before CI runs

**Example Output:**
```
Checking pyproject.toml...

✗ 2 error(s) found:
  - [tool.ruff] line-length should be 111, got 120
  - [tool.ruff.lint] select should be [...], got [...]

⚠ 1 warning(s):
  - [project] requires-python should be '>=3.11', got '>=3.9'
```

---

## Standard Configuration

All repos use this `.pre-commit-config.yaml` (distributed from `ci-tooling/configs/`):

```yaml
repos:
  # Standard checks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-toml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: debug-statements

  # Ruff - Linting and formatting
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.4
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  # Mypy - Type checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        args: [--ignore-missing-imports]

  # provide.io custom hooks
  - repo: https://github.com/provide-io/ci-tooling
    rev: v0.1.0
    hooks:
      - id: provide-conform
      - id: provide-config-check
```

---

## Installation

### Automatic (Recommended)

Use the Makefile target (already added to `Makefile.python.tmpl`):

```bash
make setup-pre-commit
```

This will:
1. Install pre-commit if not already installed
2. Copy the standard config from `ci-tooling/configs/`
3. Install git hooks
4. Display confirmation

### Manual

```bash
# Install pre-commit
pip install pre-commit

# Copy standard config
cp ../ci-tooling/configs/pre-commit-config.yaml .pre-commit-config.yaml

# Install hooks
pre-commit install
pre-commit install --hook-type commit-msg
```

---

## Developer Workflow

### Normal Commits (Hooks Auto-Fix)

```bash
# Edit code
vim src/mypackage/module.py

# Stage changes
git add src/mypackage/module.py

# Commit (hooks run automatically)
git commit -m "Add new feature"

# Output:
# SPDX Headers & Footers.......................................Fixed
# Configuration Standardization Check..........................Passed
# Ruff.........................................................Fixed
# Ruff Format..................................................Passed
# Mypy.........................................................Passed
#
# ✓ Fixed: src/mypackage/module.py
# # 🐍🔌🔚 Files modified - please review and re-add them

# Re-add auto-fixed files
git add src/mypackage/module.py

# Commit again (hooks pass this time)
git commit -m "Add new feature"
# [main abc1234] Add new feature
#  1 file changed, 10 insertions(+)
```

### Skipping Hooks (Emergencies Only)

```bash
# Skip hooks (NOT RECOMMENDED)
git commit --no-verify -m "Emergency fix"
```

⚠️ **Warning:** CI will still run all checks. Skipping hooks just delays failure detection.

### Running Hooks Manually

```bash
# Run on all files
pre-commit run --all-files

# Run on specific files
pre-commit run --files src/mypackage/module.py

# Run specific hook
pre-commit run provide-conform --all-files
```

### Updating Hooks

```bash
# Update to latest versions
pre-commit autoupdate

# This updates:
# - Standard hooks (pre-commit-hooks, ruff, mypy)
# - provide.io hooks (from ci-tooling)
```

---

## Troubleshooting

### Hook Not Found

**Error:**
```
[ERROR] An error has occurred: InvalidManifestError:
=====> /.pre-commit-config.yaml at rev 'v0.1.0'
=====> `repo: https://github.com/provide-io/ci-tooling` does not exist.
```

**Solution:**
The ci-tooling hooks haven't been published yet. Use local path temporarily:

```yaml
# In .pre-commit-config.yaml
- repo: local
  hooks:
    - id: provide-conform
      name: SPDX Headers & Footers
      entry: python -m provide.cicd.conform
      language: python
      types: [python]
```

### Wrong Footer Applied

**Problem:** Hook applies wrong footer pattern

**Solution:**
Check repository detection:

```bash
# Test detection
cd your-repo
git remote get-url origin
# Should show: github.com/provide-io/your-repo.git

# Verify registry has your repo
python -c "import json; from provide.cicd import __file__ as f; from pathlib import Path; print(json.load(open(Path(f).parent / 'footer_registry.json'))['repositories'].get('your-repo'))"
```

If your repo is missing from the registry, add it:

```json
{
  "repositories": {
    "your-repo": "# 🆕📦🔚"
  }
}
```

### Hook Runs Too Slow

**Problem:** Pre-commit hooks slow down commits

**Solutions:**

1. **Run in parallel:** Pre-commit runs hooks in parallel by default
2. **Skip slow hooks:** Add to `.pre-commit-config.yaml`:
   ```yaml
   repos:
     - repo: https://github.com/pre-commit/mirrors-mypy
       rev: v1.13.0
       hooks:
         - id: mypy
           stages: [manual]  # Only run when explicitly called
   ```
3. **Use `fail_fast`:** Stop on first failure:
   ```yaml
   fail_fast: true
   ```

### Config Check Fails

**Error:**
```
✗ 3 error(s) found:
  - [tool.ruff] line-length should be 111, got 120
  - [tool.ruff.lint] select should be [...], got [...]
  - [tool.mypy] strict should be True, got False
```

**Solution:**
Fix your `pyproject.toml` to match canonical standards. See `code-conformance-analysis.md` for required settings.

---

## CI Integration

The same hooks run in CI to catch any bypassed checks:

```yaml
# .github/workflows/conformance.yml
name: Conformance Check

on: [push, pull_request]

jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - uses: pre-commit/action@v3.0.0
```

---

## Maintenance

### Updating Central Hooks

**For ci-tooling maintainers:**

```bash
cd ci-tooling

# Edit hooks
vim src/provide/cicd/conform.py
vim src/provide/cicd/config_check.py

# Test locally
cd ../pyvider
pre-commit run provide-conform --all-files

# Commit and tag release
cd ../ci-tooling
git add src/provide/cicd/
git commit -m "Update conform hook"
git tag v0.2.0
git push origin main v0.2.0
```

All repos will get the update next time they run `pre-commit autoupdate`.

### Adding New Repository to Registry

```bash
cd ci-tooling

# Edit registry
vim src/provide/cicd/footer_registry.json

# Add entry:
{
  "repositories": {
    "new-repo": "# 🆕🔧🔚"
  }
}

# Commit
git add src/provide/cicd/footer_registry.json
git commit -m "Add footer for new-repo"
git tag v0.2.0
git push origin main v0.2.0
```

### Updating Standard Config

```bash
cd ci-tooling

# Edit template
vim configs/pre-commit-config.yaml

# Update rev versions, add hooks, etc.

# Commit
git add configs/
git commit -m "Update standard pre-commit config"
git push origin main

# Distribute to repos
cd ../pyvider
cp ../ci-tooling/configs/pre-commit-config.yaml .pre-commit-config.yaml
git add .pre-commit-config.yaml
git commit -m "Update pre-commit config from ci-tooling"
```

---

## Benefits

| Before (Manual) | After (Pre-commit) |
|----------------|-------------------|
| ❌ Remember to run `conform.py` | ✅ Automatic on commit |
| ❌ Manually specify `--footer` | ✅ Auto-detected |
| ❌ Forget to check config standards | ✅ Validated automatically |
| ❌ CI failures surprise you | ✅ Caught locally before push |
| ❌ Inconsistent formatting | ✅ Ruff formats on commit |
| ❌ Type errors in production | ✅ Mypy checks on commit |
| ⏱️ 5-10 minutes per commit | ⏱️ 10-30 seconds per commit |

---

## FAQ

**Q: Do I need to run `conform.py` anymore?**
A: No! The pre-commit hook replaces it entirely.

**Q: What if I want a different footer?**
A: Add your repo to `footer_registry.json` in ci-tooling.

**Q: Can I customize hooks per repo?**
A: Yes, edit `.pre-commit-config.yaml` locally. But standard config is recommended.

**Q: What if pre-commit isn't installed?**
A: Run `make setup-pre-commit` - it will install it for you.

**Q: Do hooks run on CI?**
A: Yes, the same hooks run via `pre-commit/action@v3.0.0`.

**Q: Can I disable a specific hook?**
A: Yes, comment it out in `.pre-commit-config.yaml` or use `SKIP`:
```bash
SKIP=mypy git commit -m "Skip mypy for this commit"
```

**Q: How do I test hooks before committing?**
A: Run `pre-commit run --all-files` manually.

---

## Next Steps

1. **Install hooks:** Run `make setup-pre-commit` in each repo
2. **Test it:** Make a commit and watch hooks auto-fix your code
3. **Spread the word:** Tell the team about zero-friction conformance
4. **Update CI:** Add conformance check workflow
5. **Iterate:** Add more hooks as needed (security, docs, etc.)

---

## Resources

- [Pre-commit documentation](https://pre-commit.com/)
- [Ruff pre-commit](https://github.com/astral-sh/ruff-pre-commit)
- [ci-tooling hooks source](https://github.com/provide-io/ci-tooling/tree/main/src/provide/cicd)
- [Code conformance analysis](./.provide/reports/code-conformance-analysis.md)

---

**Generated:** 2025-11-10
**Maintained by:** provide.io engineering team
