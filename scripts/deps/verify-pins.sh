#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT
#
# Thin runner for verify_pins.py. Runs after `uv sync`, because the point is to
# read what the resolver actually did rather than what it was asked to do.
set -euo pipefail

PY=$(command -v python3 || command -v python)

exec "$PY" "${CI_TOOLING_PATH:?}/scripts/deps/verify_pins.py" \
  --pins-json "${PINS:-[]}" \
  --lock-file "${PINS_LOCK:-uv.lock}"
