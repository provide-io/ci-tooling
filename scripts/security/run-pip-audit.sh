#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2026 provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT

# Run pip-audit to check for known vulnerabilities in dependencies
set -euo pipefail

OUTPUT_FILE="${1:-pip-audit-report.json}"

echo "🔍 Running pip-audit dependency vulnerability check"

# Run with JSON output for CI processing
pip-audit --format json --output "$OUTPUT_FILE" || true

# Run with terminal output for human readability
pip-audit || true

echo "📄 Report saved to: $OUTPUT_FILE"
