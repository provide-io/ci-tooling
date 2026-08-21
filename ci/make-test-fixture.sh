#!/usr/bin/env bash
# Generate the throwaway package + tests used to exercise the python-test action.
#
# The empty conftest.py at the repo root is load-bearing: pytest is invoked as
# `pytest test_tests/`, and under the default prepend import mode it only adds
# each test file's own basedir to sys.path. Without a root conftest.py, the
# sibling `test_src` package is not importable and collection fails with
# ModuleNotFoundError.
set -euo pipefail

mkdir -p test_src test_tests

cat > test_src/calculator.py << 'EOF'
"""Simple calculator for testing."""


def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b
EOF

cat > test_tests/test_calculator.py << 'EOF'
"""Tests for calculator."""

from test_src.calculator import add, multiply


def test_add():
    """Test addition."""
    assert add(2, 3) == 5
    assert add(-1, 1) == 0


def test_multiply():
    """Test multiplication."""
    assert multiply(3, 4) == 12
    assert multiply(0, 5) == 0
EOF

: > conftest.py

echo "✅ wrote test_src/, test_tests/, conftest.py"
