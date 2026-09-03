#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT
#
# Thin runner for resolve_pins.py. Exists so the composite action holds no logic
# and so the interpreter is picked per-platform: Windows runners have `python`
# under git-bash but not always `python3`.
#
# Every input arrives through the environment, never through interpolation into
# the command line.
set -euo pipefail

PY=$(command -v python3 || command -v python)

# Defaults are set as plain assignments rather than inline expansions: the JSON
# ones contain braces, which do not survive ${VAR:-...} cleanly.
LABEL_PINS_JSON="${LABEL_PINS_JSON:-}"
INPUTS_JSON="${INPUTS_JSON:-}"
[ -n "$LABEL_PINS_JSON" ] || LABEL_PINS_JSON="[]"
[ -n "$INPUTS_JSON" ] || INPUTS_JSON="{}"

exec "$PY" "${CI_TOOLING_PATH:?}/scripts/deps/resolve_pins.py" \
  --dispatch "${DISPATCH_PINS:-}" \
  --variable "${VARIABLE_PINS:-}" \
  --caller-input "${CALLER_PINS:-}" \
  --pins-file "${PINS_FILE:-.ci/pins.toml}" \
  --auto-siblings "${AUTO_SIBLINGS:-}" \
  --allowed-orgs "${ALLOWED_ORGS:-github.com/provide-io/*,github.com/livingstaccato/*}" \
  --labels-json "$LABEL_PINS_JSON" \
  --inputs-json "$INPUTS_JSON"
