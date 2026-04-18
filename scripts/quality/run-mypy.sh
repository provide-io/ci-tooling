#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2026 provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT

# Run MyPy type checker on Python source code
set -euo pipefail

SOURCE_PATH="${1:-src/}"
STRICT="${2:-false}"

echo "🔒 Running MyPy type check on: $SOURCE_PATH"

if [ "$STRICT" = "true" ]; then
    mypy "$SOURCE_PATH" --strict
else
    mypy "$SOURCE_PATH" --ignore-missing-imports
fi
