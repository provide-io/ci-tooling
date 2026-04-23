#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Resolve the release version from either the release event or the tag ref.
# Emits `version=X.Y.Z` on stdout for capture into $GITHUB_OUTPUT.
# Env: RELEASE_TAG (from event.release.tag_name), REF_NAME (from github.ref_name).
set -euo pipefail

TAG="${RELEASE_TAG:-${REF_NAME:-}}"
if [ -z "${TAG}" ]; then
    echo "Unable to resolve release tag from RELEASE_TAG or REF_NAME" >&2
    exit 1
fi

echo "version=${TAG#v}"
