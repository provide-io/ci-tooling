# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Pytest configuration and fixtures for provide.cicd tests."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from provide.testkit import reset_foundation_setup_for_testing

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture(autouse=True)
def reset_foundation() -> None:
    """Reset Foundation state before each test."""
    reset_foundation_setup_for_testing()


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Provide a temporary directory for tests."""
    return tmp_path


@pytest.fixture
def sample_python_file(temp_dir: Path) -> Path:
    """Create a sample Python file for testing."""
    file_path = temp_dir / "sample.py"
    file_path.write_text("def hello():\n    pass\n")
    return file_path


@pytest.fixture
def sample_python_with_shebang(temp_dir: Path) -> Path:
    """Create a sample Python file with shebang."""
    file_path = temp_dir / "executable.py"
    file_path.write_text("#!/usr/bin/env python3\n\ndef main():\n    pass\n")
    return file_path


@pytest.fixture
def sample_python_with_docstring(temp_dir: Path) -> Path:
    """Create a sample Python file with docstring."""
    file_path = temp_dir / "documented.py"
    content = '''"""Module docstring here."""

def greet(name: str) -> str:
    """Greet someone."""
    return f"Hello, {name}!"
'''
    file_path.write_text(content)
    return file_path


@pytest.fixture
def sample_python_with_footer(temp_dir: Path) -> Path:
    """Create a sample Python file with an old footer."""
    file_path = temp_dir / "with_footer.py"
    content = """def test():
    pass

# 🐍🔌🔚
"""
    file_path.write_text(content)
    return file_path


@pytest.fixture
def sample_pyproject_toml(temp_dir: Path) -> Path:
    """Create a valid pyproject.toml file."""
    file_path = temp_dir / "pyproject.toml"
    content = """[project]
name = "test-package"
version = "0.1.0"
requires-python = ">=3.11"
license = "Apache-2.0"

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
    file_path.write_text(content)
    return file_path


@pytest.fixture
def invalid_pyproject_toml(temp_dir: Path) -> Path:
    """Create an invalid pyproject.toml file."""
    file_path = temp_dir / "pyproject.toml"
    content = """[project]
name = "test-package"
version = "0.1.0"
requires-python = ">=3.9"
license = "MIT"

[tool.ruff]
line-length = 88
target-version = "py39"

[tool.mypy]
python_version = "3.9"
strict = false
"""
    file_path.write_text(content)
    return file_path


@pytest.fixture
def mock_footer_registry(temp_dir: Path) -> Path:
    """Create a mock footer registry JSON file."""
    import json

    file_path = temp_dir / "footer_registry.json"
    registry = {
        "repositories": {
            "test-repo": "# 🧪🔚",
            "pyvider": "# 🐍🔌🔚",
            "ci-tooling": "# 🧰⚙️🔚",
        },
        "default_footer": "# 🔚",
        "version": "1.0.0",
    }
    file_path.write_text(json.dumps(registry, indent=2))
    return file_path


@pytest.fixture
def mock_git_repo(temp_dir: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[Path, None, None]:
    """Create a mock git repository."""
    import subprocess

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=temp_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=temp_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=temp_dir,
        check=True,
        capture_output=True,
    )

    # Add remote
    subprocess.run(
        ["git", "remote", "add", "origin", "https://github.com/provide-io/test-repo.git"],
        cwd=temp_dir,
        check=True,
        capture_output=True,
    )

    # Change to that directory for the test
    monkeypatch.chdir(temp_dir)

    yield temp_dir


# 🧰⚙️🔚
