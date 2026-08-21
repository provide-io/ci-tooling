#!/usr/bin/env bash
# Generate the throwaway source tree used to exercise the python-quality action.
# The content must already satisfy `ruff format --check`, otherwise the action
# fails on the fixture rather than on the behaviour under test.
set -euo pipefail

mkdir -p test_src

cat > test_src/example.py << 'EOF'
"""Example Python file for testing."""


def hello_world() -> str:
    """Return a greeting."""
    return "Hello, World!"


if __name__ == "__main__":
    print(hello_world())
EOF

echo "✅ wrote test_src/example.py"
