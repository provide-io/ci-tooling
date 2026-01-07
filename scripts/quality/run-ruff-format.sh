#!/usr/bin/env bash
# Run Ruff format check on Python source code
set -euo pipefail

SOURCE_PATHS="${1:-src/ tests/}"
CHECK_ONLY="${2:-true}"

echo "🎨 Running Ruff format check on: $SOURCE_PATHS"

if [ "$CHECK_ONLY" = "true" ]; then
    ruff format --check $SOURCE_PATHS
else
    ruff format $SOURCE_PATHS
fi
