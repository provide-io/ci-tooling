#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT
#
# Assert that a resolve-pins run produced the pins we expected.
#
# Used by test-actions.yml to exercise the layers that no real caller has hit
# yet: the CI_PINS variable, a workflow_dispatch input, and sibling matching.
#
# Usage: assert-pins.sh <label> <expected-count> <substring...>
set -euo pipefail

label="$1"; expected="$2"; shift 2
actual=$(printf '%s' "${PINS:-[]}" | python3 -c 'import json,sys; print(len(json.load(sys.stdin)))')

if [ "$actual" != "$expected" ]; then
  echo "::error::$label: expected $expected pin(s), got $actual -- ${PINS:-[]}" >&2
  exit 1
fi

for needle in "$@"; do
  case "${PINS:-}" in
    *"$needle"*) ;;
    *) echo "::error::$label: expected to find '$needle' in ${PINS:-[]}" >&2; exit 1 ;;
  esac
done

echo "✅ $label: $expected pin(s), all expected substrings present"
