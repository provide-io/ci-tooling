#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT
#
# Thin runner for apply_pins.py.
#
# --no-project matters: without it `uv run` would first sync the project we are
# about to patch, which is both wasteful and wrong ordering.
set -euo pipefail

exec uv run --no-project "${CI_TOOLING_PATH:?}/scripts/deps/apply_pins.py" apply \
  --pins-json "${PINS:?}" \
  --pyproject "${PYPROJECT:-pyproject.toml}"
