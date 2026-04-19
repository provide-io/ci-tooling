#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2026 provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT
#
# Regenerate CHANGELOG.md across all sibling provide-io repos using git-cliff.
#
# Usage:
#   scripts/generate-changelogs.sh                          # default config (terse), all 19 repos
#   scripts/generate-changelogs.sh <repo> [<repo>...]       # default config, specific repos
#   scripts/generate-changelogs.sh --config <name> [repos]  # alt config (e.g. cliff-vocabulary.toml)
#   REPOS_ROOT=/path/to/pyv scripts/generate-changelogs.sh  # override parent dir
#
# Config names are relative to configs/ (e.g. cliff.toml, cliff-vocabulary.toml).
# git-cliff must be on PATH (install: `uv tool install git-cliff`).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIGS_DIR="${SCRIPT_DIR}/../configs"
REPOS_ROOT="${REPOS_ROOT:-/Volumes/data/pyv}"
CONFIG_NAME="cliff.toml"

# Parse --config flag
while [[ $# -gt 0 && "$1" == --* ]]; do
  case "$1" in
    --config)
      CONFIG_NAME="$2"
      shift 2
      ;;
    --config=*)
      CONFIG_NAME="${1#--config=}"
      shift
      ;;
    --help|-h)
      sed -n '3,16p' "${BASH_SOURCE[0]}" | sed 's/^# \?//'
      exit 0
      ;;
    *)
      echo "error: unknown flag '$1'" >&2
      exit 2
      ;;
  esac
done

CLIFF_CONFIG="${CONFIGS_DIR}/${CONFIG_NAME}"

if ! command -v git-cliff >/dev/null 2>&1; then
  echo "error: git-cliff not on PATH. Install with:" >&2
  echo "  uv tool install git-cliff    # or: cargo install git-cliff" >&2
  exit 1
fi

if [[ ! -f "${CLIFF_CONFIG}" ]]; then
  echo "error: cliff config not found at ${CLIFF_CONFIG}" >&2
  echo "available configs:" >&2
  ls "${CONFIGS_DIR}"/cliff*.toml 2>/dev/null | sed 's|^|  |' >&2
  exit 1
fi

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

echo "Using config: ${CONFIG_NAME}"
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
