#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2026 provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT
#
# Regenerate CHANGELOG.md across all sibling provide-io repos using git-cliff.
#
# Usage:
#   scripts/generate-changelogs.sh                         # run on default repo list
#   scripts/generate-changelogs.sh <repo> [<repo>...]      # run on specific repos (repo subdir name)
#   REPOS_ROOT=/path/to/pyv scripts/generate-changelogs.sh # override parent dir
#
# Assumes git-cliff is on PATH (install via `cargo install git-cliff` or `uv tool install git-cliff`).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLIFF_CONFIG="${SCRIPT_DIR}/../configs/cliff.toml"
REPOS_ROOT="${REPOS_ROOT:-/Volumes/data/pyv}"

if ! command -v git-cliff >/dev/null 2>&1; then
  echo "error: git-cliff not on PATH. Install with:" >&2
  echo "  uv tool install git-cliff    # or: cargo install git-cliff" >&2
  exit 1
fi

if [[ ! -f "${CLIFF_CONFIG}" ]]; then
  echo "error: cliff config not found at ${CLIFF_CONFIG}" >&2
  exit 1
fi

# Default repo list: every sibling provide-io repo that consumes this tooling.
DEFAULT_REPOS=(
  ci-tooling flavorpack plating provide-foundation provide-foundry
  provide-telemetry provide-terminal provide-testkit provide-workspace
  pyvider pyvider-components pyvider-cty pyvider-hcl pyvider-rpcplugin
  supsrc terraform-provider-pyvider terraform-provider-tofusoup tofusoup
  wrknv
)

if [[ $# -gt 0 ]]; then
  REPOS=("$@")
else
  REPOS=("${DEFAULT_REPOS[@]}")
fi

printf "%-32s %s\n" "repo" "status"
printf "%-32s %s\n" "----" "------"

for repo in "${REPOS[@]}"; do
  repo_dir="${REPOS_ROOT}/${repo}"
  if [[ ! -d "${repo_dir}/.git" ]]; then
    printf "%-32s missing\n" "${repo}"
    continue
  fi

  if git-cliff --config "${CLIFF_CONFIG}" --repository "${repo_dir}" --output "${repo_dir}/CHANGELOG.md" >/dev/null 2>&1; then
    lines=$(wc -l < "${repo_dir}/CHANGELOG.md" | tr -d ' ')
    printf "%-32s ✓ (%s lines)\n" "${repo}" "${lines}"
  else
    printf "%-32s ✗ (git-cliff failed)\n" "${repo}"
  fi
done
