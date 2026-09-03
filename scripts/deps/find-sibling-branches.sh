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
set -euo pipefail

found=()
for repo in ${SIBLINGS//,/ }; do
  if gh api "repos/${OWNER:?}/${repo}/branches/${BRANCH:?}" --silent >/dev/null 2>&1; then
    found+=("$repo")
  fi
done

printf 'found=%s\n' "$(IFS=,; echo "${found[*]-}")" >> "${GITHUB_OUTPUT:?}"
