#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2026 provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT

# Run Ruff linter on Python source code
set -euo pipefail

SOURCE_PATHS="${1:-src/ tests/}"
FIX="${2:-false}"

echo "🔍 Running Ruff lint on: $SOURCE_PATHS"

if [ "$FIX" = "true" ]; then
    ruff check --fix $SOURCE_PATHS
else
    ruff check $SOURCE_PATHS
fi
