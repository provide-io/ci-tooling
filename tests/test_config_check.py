# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for provide.cicd.config_check module."""

from __future__ import annotations

from pathlib import Path

from provide.cicd.config_check import (
    CANONICAL_MYPY,
    CANONICAL_RUFF,
    CANONICAL_RUFF_FORMAT,
    CANONICAL_RUFF_LINT_IGNORE,
    CANONICAL_RUFF_LINT_SELECT,
    REQUIRED_PYTEST_SETTINGS,
    check_mypy_config,
    check_project_metadata,
    check_pytest_config,
    check_ruff_config,
    validate_pyproject,
)

# ==============================================================================
# Test check_ruff_config
# ==============================================================================


def test_check_ruff_config_valid(sample_pyproject_toml: Path) -> None:
    """Test ruff config validation with valid configuration."""
    import tomllib

    with sample_pyproject_toml.open("rb") as f:
        config = tomllib.load(f)

    errors = check_ruff_config(config)

    assert errors == []


def test_check_ruff_config_invalid_line_length(temp_dir: Path) -> None:
    """Test ruff config validation with invalid line length."""
    import tomllib

    pyproject = temp_dir / "pyproject.toml"
    content = """
[tool.ruff]
line-length = 88
indent-width = 4
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "ANN", "B", "C90", "SIM", "PTH", "RUF"]
ignore = ["ANN401", "B008", "E501"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
    pyproject.write_text(content)

    with pyproject.open("rb") as f:
        config = tomllib.load(f)

    errors = check_ruff_config(config)

    assert len(errors) > 0
    assert any("line-length" in error and "111" in error for error in errors)


def test_check_ruff_config_missing_lint_select(temp_dir: Path) -> None:
    """Test ruff config validation with missing lint select."""
    import tomllib

    pyproject = temp_dir / "pyproject.toml"
    content = """
[tool.ruff]
line-length = 111
indent-width = 4
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F"]
ignore = ["ANN401", "B008", "E501"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
    pyproject.write_text(content)

    with pyproject.open("rb") as f:
        config = tomllib.load(f)

    errors = check_ruff_config(config)

    assert len(errors) > 0
    assert any("select" in error for error in errors)


def test_check_ruff_config_wrong_format(temp_dir: Path) -> None:
    """Test ruff config validation with wrong format settings."""
    import tomllib

    pyproject = temp_dir / "pyproject.toml"
    content = """
[tool.ruff]
line-length = 111
indent-width = 4
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "ANN", "B", "C90", "SIM", "PTH", "RUF"]
ignore = ["ANN401", "B008", "E501"]

[tool.ruff.format]
quote-style = "single"
indent-style = "tab"
skip-magic-trailing-comma = true
line-ending = "lf"
"""
    pyproject.write_text(content)

    with pyproject.open("rb") as f:
        config = tomllib.load(f)

    errors = check_ruff_config(config)

    assert len(errors) >= 4  # At least 4 format errors
    assert any("quote-style" in error for error in errors)
    assert any("indent-style" in error for error in errors)


def test_check_ruff_config_missing_section(temp_dir: Path) -> None:
    """Test ruff config validation with missing ruff section."""
    import tomllib

    pyproject = temp_dir / "pyproject.toml"
    content = """
[project]
name = "test"
"""
    pyproject.write_text(content)

    with pyproject.open("rb") as f:
        config = tomllib.load(f)

    errors = check_ruff_config(config)

    assert len(errors) > 0  # Should have errors for missing values


# ==============================================================================
# Test check_mypy_config
# ==============================================================================


def test_check_mypy_config_valid(sample_pyproject_toml: Path) -> None:
    """Test mypy config validation with valid configuration."""
    import tomllib

    with sample_pyproject_toml.open("rb") as f:
        config = tomllib.load(f)

    errors = check_mypy_config(config)

    assert errors == []


def test_check_mypy_config_invalid_python_version(temp_dir: Path) -> None:
    """Test mypy config validation with invalid Python version."""
    import tomllib

    pyproject = temp_dir / "pyproject.toml"
    content = """
[tool.mypy]
python_version = "3.9"
strict = true
pretty = true
show_error_codes = true
show_column_numbers = true
warn_unused_ignores = true
warn_unused_configs = true
"""
    pyproject.write_text(content)

    with pyproject.open("rb") as f:
        config = tomllib.load(f)

    errors = check_mypy_config(config)

    assert len(errors) > 0
    assert any("python_version" in error and "3.11" in error for error in errors)


def test_check_mypy_config_strict_false(temp_dir: Path) -> None:
    """Test mypy config validation with strict=false."""
    import tomllib

    pyproject = temp_dir / "pyproject.toml"
    content = """
[tool.mypy]
python_version = "3.11"
strict = false
pretty = true
show_error_codes = true
show_column_numbers = true
warn_unused_ignores = true
warn_unused_configs = true
"""
    pyproject.write_text(content)

    with pyproject.open("rb") as f:
        config = tomllib.load(f)

    errors = check_mypy_config(config)

    assert len(errors) > 0
    assert any("strict" in error and "True" in error for error in errors)


def test_check_mypy_config_missing_required_fields(temp_dir: Path) -> None:
    """Test mypy config validation with missing required fields."""
    import tomllib

    pyproject = temp_dir / "pyproject.toml"
    content = """
[tool.mypy]
python_version = "3.11"
"""
    pyproject.write_text(content)

    with pyproject.open("rb") as f:
        config = tomllib.load(f)

    errors = check_mypy_config(config)

    # Should have errors for missing strict, pretty, etc.
    assert len(errors) >= 5


# ==============================================================================
# Test check_pytest_config
# ==============================================================================


def test_check_pytest_config_valid(sample_pyproject_toml: Path) -> None:
    """Test pytest config validation with valid configuration."""
    import tomllib

    with sample_pyproject_toml.open("rb") as f:
        config = tomllib.load(f)

    errors = check_pytest_config(config)

    assert errors == []


def test_check_pytest_config_log_cli_false(temp_dir: Path) -> None:
    """Test pytest config validation with log_cli=false."""
    import tomllib

    pyproject = temp_dir / "pyproject.toml"
    content = """
[tool.pytest.ini_options]
log_cli = false
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
"""
    pyproject.write_text(content)

    with pyproject.open("rb") as f:
        config = tomllib.load(f)

    errors = check_pytest_config(config)

    assert len(errors) > 0
    assert any("log_cli" in error and "True" in error for error in errors)


def test_check_pytest_config_wrong_testpaths(temp_dir: Path) -> None:
    """Test pytest config validation with wrong testpaths."""
    import tomllib

    pyproject = temp_dir / "pyproject.toml"
    content = """
[tool.pytest.ini_options]
log_cli = true
testpaths = ["spec"]
python_files = ["test_*.py", "*_test.py"]
"""
    pyproject.write_text(content)

    with pyproject.open("rb") as f:
        config = tomllib.load(f)

    errors = check_pytest_config(config)

    assert len(errors) > 0
    assert any("testpaths" in error for error in errors)


def test_check_pytest_config_missing_python_files(temp_dir: Path) -> None:
    """Test pytest config validation with missing python_files."""
    import tomllib

    pyproject = temp_dir / "pyproject.toml"
    content = """
[tool.pytest.ini_options]
log_cli = true
testpaths = ["tests"]
"""
    pyproject.write_text(content)

    with pyproject.open("rb") as f:
        config = tomllib.load(f)

    errors = check_pytest_config(config)

    assert len(errors) > 0
    assert any("python_files" in error for error in errors)


# ==============================================================================
# Test check_project_metadata
# ==============================================================================


def test_check_project_metadata_valid(sample_pyproject_toml: Path) -> None:
    """Test project metadata validation with valid configuration."""
    import tomllib

    with sample_pyproject_toml.open("rb") as f:
        config = tomllib.load(f)

    warnings = check_project_metadata(config)

    assert warnings == []


def test_check_project_metadata_wrong_license(temp_dir: Path) -> None:
    """Test project metadata validation with wrong license."""
    import tomllib

    pyproject = temp_dir / "pyproject.toml"
    content = """
[project]
name = "test"
license = "MIT"
requires-python = ">=3.11"
"""
    pyproject.write_text(content)

    with pyproject.open("rb") as f:
        config = tomllib.load(f)

    warnings = check_project_metadata(config)

    assert len(warnings) > 0
    assert any("license" in warning and "Apache-2.0" in warning for warning in warnings)


def test_check_project_metadata_old_python_version(temp_dir: Path) -> None:
    """Test project metadata validation with old Python version."""
    import tomllib

    pyproject = temp_dir / "pyproject.toml"
    content = """
[project]
name = "test"
license = "Apache-2.0"
requires-python = ">=3.9"
"""
    pyproject.write_text(content)

    with pyproject.open("rb") as f:
        config = tomllib.load(f)

    warnings = check_project_metadata(config)

    assert len(warnings) > 0
    assert any("requires-python" in warning and ">=3.11" in warning for warning in warnings)


# ==============================================================================
# Test validate_pyproject
# ==============================================================================


def test_validate_pyproject_valid(sample_pyproject_toml: Path) -> None:
    """Test full pyproject.toml validation with valid file."""
    errors, warnings = validate_pyproject(sample_pyproject_toml)

    assert errors == []
    assert warnings == []


def test_validate_pyproject_invalid(invalid_pyproject_toml: Path) -> None:
    """Test full pyproject.toml validation with invalid file."""
    errors, warnings = validate_pyproject(invalid_pyproject_toml)

    # Should have multiple errors
    assert len(errors) > 0
    # Should have warnings about license and Python version
    assert len(warnings) > 0


def test_validate_pyproject_nonexistent_file(temp_dir: Path) -> None:
    """Test validation with non-existent file."""
    nonexistent = temp_dir / "nonexistent.toml"

    errors, _warnings = validate_pyproject(nonexistent)

    assert len(errors) > 0
    assert any("Failed to parse" in error for error in errors)


def test_validate_pyproject_corrupt_toml(temp_dir: Path) -> None:
    """Test validation with corrupt TOML file."""
    corrupt = temp_dir / "corrupt.toml"
    corrupt.write_text("[invalid toml content")

    errors, _warnings = validate_pyproject(corrupt)

    assert len(errors) > 0
    assert any("Failed to parse" in error for error in errors)


def test_validate_pyproject_empty_file(temp_dir: Path) -> None:
    """Test validation with empty file."""
    empty = temp_dir / "empty.toml"
    empty.write_text("")

    errors, _warnings = validate_pyproject(empty)

    # Empty file should load but have many missing config errors
    assert len(errors) > 0


# ==============================================================================
# Test Constants
# ==============================================================================


def test_constants_are_defined() -> None:
    """Test that all expected constants are defined."""
    assert CANONICAL_RUFF["line-length"] == 111
    assert CANONICAL_RUFF["target-version"] == "py311"

    assert "E" in CANONICAL_RUFF_LINT_SELECT
    assert "ANN401" in CANONICAL_RUFF_LINT_IGNORE

    assert CANONICAL_RUFF_FORMAT["quote-style"] == "double"

    assert CANONICAL_MYPY["python_version"] == "3.11"
    assert CANONICAL_MYPY["strict"] is True

    assert REQUIRED_PYTEST_SETTINGS["log_cli"] is True
    assert REQUIRED_PYTEST_SETTINGS["testpaths"] == ["tests"]


def test_canonical_ruff_lint_select_has_required_rules() -> None:
    """Test that canonical ruff lint select has all required rules."""
    required_rules = ["E", "F", "W", "I", "UP", "ANN", "B", "RUF"]

    for rule in required_rules:
        assert rule in CANONICAL_RUFF_LINT_SELECT


# ==============================================================================
# Test main() CLI function
# ==============================================================================


def test_main_with_valid_pyproject(sample_pyproject_toml: Path) -> None:
    """Test main() CLI with valid pyproject.toml."""
    from provide.cicd.config_check import main

    exit_code = main([str(sample_pyproject_toml)])

    # Should exit successfully
    assert exit_code == 0


def test_main_with_invalid_pyproject(invalid_pyproject_toml: Path) -> None:
    """Test main() with invalid pyproject.toml."""
    from provide.cicd.config_check import main

    exit_code = main([str(invalid_pyproject_toml)])

    # Should exit with error code 1
    assert exit_code == 1


def test_main_with_warnings_not_strict(temp_dir: Path) -> None:
    """Test main() with warnings but not strict mode."""
    from provide.cicd.config_check import main

    # Create pyproject.toml with only warnings (wrong license)
    pyproject = temp_dir / "pyproject.toml"
    content = """[project]
name = "test"
license = "MIT"
requires-python = ">=3.11"

[tool.ruff]
line-length = 111
indent-width = 4
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "ANN", "B", "C90", "SIM", "PTH", "RUF"]
ignore = ["ANN401", "B008", "E501"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"

[tool.mypy]
python_version = "3.11"
mypy_path = "src"
strict = true
pretty = true
show_error_codes = true
show_column_numbers = true
warn_unused_ignores = true
warn_unused_configs = true

[tool.pytest.ini_options]
log_cli = true
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
"""
    pyproject.write_text(content)

    # Call without --strict
    exit_code = main([str(pyproject)])

    # Warnings don't fail without --strict
    assert exit_code == 0


def test_main_with_warnings_strict_mode(temp_dir: Path) -> None:
    """Test main() with warnings in strict mode."""
    from provide.cicd.config_check import main

    # Create pyproject.toml with only warnings (wrong license)
    pyproject = temp_dir / "pyproject.toml"
    content = """[project]
name = "test"
license = "MIT"
requires-python = ">=3.11"

[tool.ruff]
line-length = 111
indent-width = 4
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "ANN", "B", "C90", "SIM", "PTH", "RUF"]
ignore = ["ANN401", "B008", "E501"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"

[tool.mypy]
python_version = "3.11"
mypy_path = "src"
strict = true
pretty = true
show_error_codes = true
show_column_numbers = true
warn_unused_ignores = true
warn_unused_configs = true

[tool.pytest.ini_options]
log_cli = true
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
"""
    pyproject.write_text(content)

    # Call with --strict
    exit_code = main([str(pyproject), "--strict"])

    # Warnings should fail in strict mode
    assert exit_code == 1


def test_main_with_no_files() -> None:
    """Test main() with no file arguments."""
    from provide.cicd.config_check import main

    exit_code = main([])

    # Should exit successfully
    assert exit_code == 0


def test_main_with_nonexistent_file(temp_dir: Path) -> None:
    """Test main() with non-existent file."""
    from provide.cicd.config_check import main

    nonexistent = temp_dir / "pyproject.toml"
    exit_code = main([str(nonexistent)])

    # Should exit with error
    assert exit_code == 1


def test_main_with_non_pyproject_file(temp_dir: Path) -> None:
    """Test main() skips non-pyproject.toml files."""
    from provide.cicd.config_check import main

    # Create a different .toml file
    other_toml = temp_dir / "other.toml"
    other_toml.write_text("[section]\nkey = 'value'\n")

    exit_code = main([str(other_toml)])

    # Should skip non-pyproject.toml files
    assert exit_code == 0


def test_main_with_multiple_files_mixed(
    sample_pyproject_toml: Path,
    invalid_pyproject_toml: Path,
) -> None:
    """Test main() with multiple files with mixed results."""
    from provide.cicd.config_check import main

    # Call with both valid and invalid
    exit_code = main([str(sample_pyproject_toml), str(invalid_pyproject_toml)])

    # Should fail because one is invalid
    assert exit_code == 1


# 🧰⚙️🔚
