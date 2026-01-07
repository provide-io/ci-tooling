#!/usr/bin/env bash
# Run pytest with coverage
set -euo pipefail

TEST_DIR="${1:-tests/}"
COV_THRESHOLD="${2:-80}"
PARALLEL="${3:-true}"

echo "🧪 Running pytest on: $TEST_DIR"

PYTEST_ARGS="$TEST_DIR --cov --cov-report=xml --cov-report=term -v"

if [ "$PARALLEL" = "true" ]; then
    PYTEST_ARGS="$PYTEST_ARGS -n auto"
fi

if [ "$COV_THRESHOLD" != "0" ]; then
    PYTEST_ARGS="$PYTEST_ARGS --cov-fail-under=$COV_THRESHOLD"
fi

pytest $PYTEST_ARGS
