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

receipt="${PINS_RECEIPT:-.ci/.pins-applied.json}"
[ -f "$receipt" ] || exit 0

echo "error: branch pins are currently applied ($receipt exists)." >&2
echo "       pyproject.toml and uv.lock are patched; clear the pins before committing." >&2
exit 1
