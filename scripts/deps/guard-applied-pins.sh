#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT
#
# Block a commit made while branch pins are applied to the working tree.
#
# Applying pins rewrites pyproject.toml and lets uv re-lock, so committing in
# that state would bake a git ref into files that must stay registry-clean.
# Run `we run deps.unpin` (or apply_pins.py clear) first.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
receipt="${PINS_RECEIPT:-.ci/.pins-applied.json}"

if [ -f "$receipt" ]; then
  echo "error: branch pins are currently applied ($receipt exists)." >&2
  echo "       pyproject.toml and uv.lock are patched; clear the pins before committing." >&2
  exit 1
fi

# Clearing the pins restores pyproject.toml but does not re-lock, so uv.lock can
# still carry the overrides after the receipt is gone. /dev/null stands in for the
# pins file: committing .ci/pins.toml itself is the point of that layer, not a fault.
PY=$(command -v python3 || command -v python)
exec "$PY" "$here/check_no_pins.py" --pins-file /dev/null --lock-file "${PINS_LOCK:-uv.lock}"
