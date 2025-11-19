#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Pre-commit hook to validate configuration standardization.

Checks that pyproject.toml configurations for ruff, mypy, and pytest
match the canonical standards for the provide.io ecosystem.

Usage as pre-commit hook:
    Automatically invoked by pre-commit when pyproject.toml changes.

Usage standalone:
    python -m provide.cicd.config_check pyproject.toml
"""

import argparse
from pathlib import Path
import sys

from provide.foundation.console.output import perr, pout

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Fallback for older Python

# --- Canonical Configuration Standards ---

CANONICAL_RUFF = {
    "line-length": 111,
    "indent-width": 4,
    "target-version": "py311",
}

CANONICAL_RUFF_LINT_SELECT = ["E", "F", "W", "I", "UP", "ANN", "B", "C90", "SIM", "PTH", "RUF"]
CANONICAL_RUFF_LINT_IGNORE = ["ANN401", "B008", "E501"]

CANONICAL_RUFF_FORMAT = {
    "quote-style": "double",
    "indent-style": "space",
    "skip-magic-trailing-comma": False,
    "line-ending": "auto",
}

CANONICAL_MYPY = {
    "python_version": "3.11",
    "strict": True,
    "pretty": True,
    "show_error_codes": True,
    "show_column_numbers": True,
    "warn_unused_ignores": True,
    "warn_unused_configs": True,
}

REQUIRED_PYTEST_SETTINGS = {
    "log_cli": True,
    "testpaths": ["tests"],
    "python_files": ["test_*.py", "*_test.py"],
}

# --- Validation Functions ---


def check_ruff_config(config: dict) -> list[str]:
    """Validate ruff configuration matches canonical standards.

    Args:
        config: Full pyproject.toml config dict

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    ruff = config.get("tool", {}).get("ruff", {})

    # Check core settings
    for key, expected_value in CANONICAL_RUFF.items():
        actual_value = ruff.get(key)
        if actual_value != expected_value:
            errors.append(f"[tool.ruff] {key} should be {expected_value!r}, got {actual_value!r}")

    # Check lint.select
    lint = ruff.get("lint", {})
    select = lint.get("select", [])
    if set(select) != set(CANONICAL_RUFF_LINT_SELECT):
        errors.append(f"[tool.ruff.lint] select should be {CANONICAL_RUFF_LINT_SELECT}, got {select}")

    # Check lint.ignore
    ignore = lint.get("ignore", [])
    if set(ignore) != set(CANONICAL_RUFF_LINT_IGNORE):
        errors.append(f"[tool.ruff.lint] ignore should be {CANONICAL_RUFF_LINT_IGNORE}, got {ignore}")

    # Check format settings
    fmt = ruff.get("format", {})
    for key, expected_value in CANONICAL_RUFF_FORMAT.items():
        actual_value = fmt.get(key)
        if actual_value != expected_value:
            errors.append(f"[tool.ruff.format] {key} should be {expected_value!r}, got {actual_value!r}")

    return errors


def check_mypy_config(config: dict) -> list[str]:
    """Validate mypy configuration matches canonical standards.

    Args:
        config: Full pyproject.toml config dict

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    mypy = config.get("tool", {}).get("mypy", {})

    for key, expected_value in CANONICAL_MYPY.items():
        actual_value = mypy.get(key)
        if actual_value != expected_value:
            errors.append(f"[tool.mypy] {key} should be {expected_value!r}, got {actual_value!r}")

    return errors


def check_pytest_config(config: dict) -> list[str]:
    """Validate pytest configuration has required settings.

    Args:
        config: Full pyproject.toml config dict

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    pytest = config.get("tool", {}).get("pytest", {}).get("ini_options", {})

    for key, expected_value in REQUIRED_PYTEST_SETTINGS.items():
        actual_value = pytest.get(key)
        if actual_value != expected_value:
            errors.append(
                f"[tool.pytest.ini_options] {key} should be {expected_value!r}, got {actual_value!r}"
            )

    return errors


def check_project_metadata(config: dict) -> list[str]:
    """Validate project metadata has required fields.

    Args:
        config: Full pyproject.toml config dict

    Returns:
        List of warning messages (empty if valid)
    """
    warnings = []

    project = config.get("project", {})

    # Check license
    license_val = project.get("license")
    if license_val != "Apache-2.0":
        warnings.append(f"[project] license should be 'Apache-2.0', got {license_val!r}")

    # Check Python version
    requires_python = project.get("requires-python", "")
    if not requires_python.startswith(">=3.11"):
        warnings.append(f"[project] requires-python should be '>=3.11', got {requires_python!r}")

    return warnings


def validate_pyproject(filepath: Path) -> tuple[list[str], list[str]]:
    """Validate a pyproject.toml file.

    Args:
        filepath: Path to pyproject.toml

    Returns:
        Tuple of (errors, warnings)
    """
    try:
        with filepath.open("rb") as f:
            config = tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError) as e:
        return ([f"Failed to parse {filepath}: {e}"], [])

    errors = []
    warnings = []

    # Run all checks
    errors.extend(check_ruff_config(config))
    errors.extend(check_mypy_config(config))
    errors.extend(check_pytest_config(config))
    warnings.extend(check_project_metadata(config))

    return errors, warnings


# --- Main Entry Point ---


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Parse command line arguments.

    Args:
        argv: Command line arguments

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Validate pyproject.toml configuration standardization",
    )
    parser.add_argument(
        "filenames",
        nargs="*",
        help="pyproject.toml files to check",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors",
    )
    return parser.parse_args(argv)


def _validate_file(filepath: Path, strict: bool) -> bool:
    """Validate a single pyproject.toml file.

    Args:
        filepath: Path to pyproject.toml file
        strict: Whether to treat warnings as errors

    Returns:
        True if file is valid, False otherwise
    """
    if not filepath.exists():
        perr(f"✗ File not found: {filepath}")
        return False

    pout(f"\nChecking {filepath}...")
    errors, warnings = validate_pyproject(filepath)

    if errors:
        pout(f"\n✗ {len(errors)} error(s) found:")
        for error in errors:
            pout(f"  - {error}")
        return False

    if warnings:
        pout(f"\n⚠ {len(warnings)} warning(s):")
        for warning in warnings:
            pout(f"  - {warning}")
        if strict:
            return False

    if not errors and (not warnings or not strict):
        pout("✓ Configuration valid")

    return True


def main(argv: list[str] | None = None) -> int:
    """Main entry point for pre-commit hook.

    Args:
        argv: Command line arguments

    Returns:
        Exit code (0 = valid, 1 = invalid)
    """
    args = _parse_args(argv)

    if not args.filenames:
        perr("No files specified")
        return 0

    all_valid = True
    for filename in args.filenames:
        filepath = Path(filename)

        if filepath.name != "pyproject.toml":
            continue  # Skip non-pyproject.toml files

        if not _validate_file(filepath, args.strict):
            all_valid = False

    return 0 if all_valid else 1


if __name__ == "__main__":
    sys.exit(main())

# 🧰⚙️🔚
