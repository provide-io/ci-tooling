#!/usr/bin/env bash
set -euo pipefail

# Run CI tasks using wrknv if available, otherwise fall back to manual commands
#
# Environment variables:
#   WORKENV_PATH - Path to virtual environment (default: .venv)
#   FALLBACK_QUALITY - Quality check command if no wrknv
#   FALLBACK_TEST - Test command if no wrknv
#   FALLBACK_BUILD - Build command if no wrknv

WORKENV_PATH="${WORKENV_PATH:-.venv}"
FALLBACK_QUALITY="${FALLBACK_QUALITY:-ruff check . && ruff format --check . && mypy src/}"
FALLBACK_TEST="${FALLBACK_TEST:-pytest}"
FALLBACK_BUILD="${FALLBACK_BUILD:-uv build}"

# Activate virtual environment
if [[ -f "${WORKENV_PATH}/bin/activate" ]]; then
    # shellcheck disable=SC1091
    source "${WORKENV_PATH}/bin/activate"
elif [[ -f "${WORKENV_PATH}/Scripts/activate" ]]; then
    # Windows
    # shellcheck disable=SC1091
    source "${WORKENV_PATH}/Scripts/activate"
else
    echo "::error::Virtual environment not found at ${WORKENV_PATH}"
    exit 1
fi

# Check for wrknv.toml
if [[ -f "wrknv.toml" ]]; then
    echo "::group::Installing wrknv"
    uv pip install --python "${WORKENV_PATH}/bin/python" "wrknv @ https://github.com/provide-io/wrknv/releases/download/v0.3.0/wrknv-0.3.0-py3-none-any.whl"
    echo "::endgroup::"

    echo "::group::Running CI tasks with wrknv"
    we run ci
    echo "::endgroup::"
else
    echo "::notice::No wrknv.toml found, using fallback commands"

    echo "::group::Quality checks"
    eval "${FALLBACK_QUALITY}"
    echo "::endgroup::"

    echo "::group::Tests"
    eval "${FALLBACK_TEST}"
    echo "::endgroup::"

    echo "::group::Build"
    eval "${FALLBACK_BUILD}"
    echo "::endgroup::"
fi
