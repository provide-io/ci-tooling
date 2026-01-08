#!/usr/bin/env bash
# Run Bandit security scanner on Python source code
set -euo pipefail

SOURCE_PATH="${1:-src/}"
OUTPUT_FILE="${2:-bandit-report.json}"
SEVERITY="${3:--ll}"

echo "🔒 Running Bandit security scan on: $SOURCE_PATH"

# Run with JSON output for CI processing
bandit -r "$SOURCE_PATH" -f json -o "$OUTPUT_FILE" "$SEVERITY" || true

# Run with terminal output for human readability
bandit -r "$SOURCE_PATH" "$SEVERITY"

echo "📄 Report saved to: $OUTPUT_FILE"
