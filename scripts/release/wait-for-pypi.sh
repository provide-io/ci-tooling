#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Block until a just-published version is installable from PyPI.
#
# Upload returning 200 is not the same as the version being resolvable. PyPI
# serves the simple index through a CDN, and for a minute or several a resolver
# asking for the new version is told it does not exist:
#
#   ERROR: Could not find a version that satisfies the requirement
#          pyvider-rpcplugin==0.5.3 (from versions: ..., 0.5.1, 0.5.2)
#
# A release workflow that ends at upload reports success into that window, so
# anything triggered off it -- a downstream floor bump, a packaging build that
# pins the exact version -- fails on a package that is genuinely published. The
# failure is invisible in the publishing repo and lands in someone else's CI.
#
# What this buys is precise: the publishing run goes red rather than green when
# the index does not catch up. It does not hold a release open. A workflow
# triggered by `release: published` has already published before this runs, and
# a consumer reacting to that event can still beat the index; preventing that
# means publishing the release only after verification, which is a change to
# the release flow rather than to this script.
#
# Resolution is checked with `pip index versions`, which reads the same index
# through the same CDN a consumer's resolver does. Asking PyPI's JSON API
# instead would answer from a different cache and clear while consumers still
# fail, which is exactly the false green this exists to prevent.
#
# Usage: wait-for-pypi.sh <package-name> <version> [timeout-seconds]
set -euo pipefail

PKG_NAME="${1:?package name required}"
PKG_VER="${2:?version required}"
TIMEOUT="${3:-600}"
INTERVAL=15

deadline=$(( $(date +%s) + TIMEOUT ))
attempt=0

while :; do
    attempt=$(( attempt + 1 ))
    # Captured before matching, not piped into `grep -q`: under `pipefail` the
    # early exit of a quiet grep SIGPIPEs pip, the pipeline reports failure, and
    # a version that is present reads as missing. `|| true` keeps a genuine pip
    # failure (no such package yet) on the retry path rather than aborting.
    versions="$(pip index versions "${PKG_NAME}" --index-url https://pypi.org/simple/ 2>/dev/null || true)"

    # Anchored on the separators the listing uses, so 0.5.3 does not match
    # 0.5.30. The version is escaped because its dots are regex wildcards.
    escaped="${PKG_VER//./\\.}"
    if printf '%s' "${versions}" | grep -qE "(^|[ ,(])${escaped}([ ,)]|\$)"; then
        echo "✅ ${PKG_NAME}==${PKG_VER} is resolvable from PyPI (attempt ${attempt})"
        exit 0
    fi

    now=$(date +%s)
    if [ "${now}" -ge "${deadline}" ]; then
        echo "::error::${PKG_NAME}==${PKG_VER} still not resolvable from PyPI after ${TIMEOUT}s." >&2
        echo "The upload may have succeeded while the index has not caught up. Anything" >&2
        echo "downstream that pins this version will fail until it does." >&2
        exit 1
    fi

    echo "… not visible yet (attempt ${attempt}); waiting ${INTERVAL}s"
    sleep "${INTERVAL}"
done
