#!/usr/bin/env bash
# Audit the calling project's dependencies for known vulnerabilities.
#
# The subject is the resolved lock, and pip-audit runs from `uvx`. Both halves
# matter. This used to run pip-audit from the project's own virtualenv, which
# the workflow had just installed it into:
#
#     uv sync --group dev
#     source .venv/bin/activate
#     uv pip install bandit pip-audit
#     pip-audit || true
#
# pip-audit audits the environment it is running in, so every advisory against
# its own dependency tree was reported as the caller's. wrknv hit the visible
# version of that: `safety` pulled in `nltk`, `nltk` drew an unpatched
# advisory, and the build went red over a package absent from the lock.
#
# `uvx` puts the scanner somewhere the audit cannot see, and the lock is a
# stable subject -- what the project resolves, unchanged by what a scanner
# happens to require this month.
set -euo pipefail

OUTPUT_FILE="${1:-pip-audit-report.json}"
# Whether a finding fails the build. Default false, which is what this script
# has always done: every call site wrapped it in `|| true`. Callers that want
# the audit to gate pass "true" -- see `fail-on-vulnerability` in the reusable
# workflows.
FAIL_ON_VULNERABILITY="${2:-false}"

echo "🔍 Running pip-audit dependency vulnerability check"

# A full mktemp template rather than `-t <prefix>`: GNU mktemp requires the
# trailing X's that BSD mktemp does not, so the short form runs on a developer's
# macOS and fails on the runner.
REQUIREMENTS="$(mktemp "${TMPDIR:-/tmp}/pip-audit-requirements.XXXXXX")"
trap 'rm -f "${REQUIREMENTS}"' EXIT

# Everything the lock resolves, dev groups included -- a vulnerable test-time
# dependency is still worth knowing about. Workspace members are left out: they
# are the project rather than something it depends on, and they are not on PyPI
# for pip-audit to look up. Their dependencies stay, since the export is the
# whole resolved graph minus the members themselves.
uv export --no-emit-workspace --format requirements-txt > "${REQUIREMENTS}"
echo "📦 Auditing $(grep -c '==' "${REQUIREMENTS}") locked packages"

# The export is fully pinned, so `--no-deps` is accurate; `--disable-pip` stops
# pip-audit building a throwaway virtualenv to resolve with, which it does even
# for a pinned file and which fails where ensurepip cannot run.
AUDIT=(uvx pip-audit --no-deps --disable-pip --requirement "${REQUIREMENTS}")

# JSON for CI processing, then a human-readable pass. The JSON run is always
# tolerant so the report artifact exists either way; the second run is the one
# whose status is allowed to matter.
"${AUDIT[@]}" --format json --output "${OUTPUT_FILE}" || true

if [ "${FAIL_ON_VULNERABILITY}" = "true" ]; then
  "${AUDIT[@]}" --desc
else
  "${AUDIT[@]}" --desc || true
fi

echo "📄 Report saved to: ${OUTPUT_FILE}"
