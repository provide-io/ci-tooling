#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT
#
# Emit `found=<comma list>` for the sibling repos that have a branch matching the
# current head ref. The network lookup lives here so the resolver itself stays a
# pure, offline, stdlib-only function.
#
# Inputs arrive through the environment: OWNER, BRANCH, SIBLINGS (comma or
# newline separated), GH_TOKEN, GITHUB_OUTPUT.
#
# An empty SIBLINGS means "work it out": the candidates are this project's own
# dependencies, so no caller has to keep a list of its siblings in step. Names
# that are not repositories in the org 404 here and drop out, which is the
# filtering, so none is attempted earlier.
set -euo pipefail

PY=$(command -v python3 || command -v python)
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -z "${SIBLINGS:-}" ]; then
  SIBLINGS=$("$PY" "$here/list_siblings.py" --pyproject "${PINS_PYPROJECT:-pyproject.toml}" | paste -sd, -)
  echo "no sibling-repos given; considering this project's dependencies: ${SIBLINGS:-<none>}"
fi

found=()
for repo in ${SIBLINGS//,/ }; do
  if gh api "repos/${OWNER:?}/${repo}/branches/${BRANCH:?}" --silent >/dev/null 2>&1; then
    found+=("$repo")
  fi
done

printf 'found=%s\n' "$(IFS=,; echo "${found[*]-}")" >> "${GITHUB_OUTPUT:?}"
