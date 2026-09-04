#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT
#
# Thin runner for require_no_pins.py. Its own job, so a pinned pull request can
# still show green tests while this one check stays red.
set -euo pipefail

PY=$(command -v python3 || command -v python)

exec "$PY" "${CI_TOOLING_PATH:?}/scripts/deps/require_no_pins.py" \
  --pins-json "${PINS:-[]}" \
  --enforce "${ENFORCE:-true}"
