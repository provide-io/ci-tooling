#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Install a package from TestPyPI with retry/propagation tolerance and then
# execute a caller-supplied import snippet to assert the installed version.
#
# Usage: verify-testpypi.sh <package-name> <version> <import-snippet>
# The import snippet must bind a variable `v` to the version, e.g.
#   "import wrknv; v = wrknv.__version__"
#   "from provide.foundation import __version__; v = __version__"
set -euo pipefail

PKG_NAME="${1:?package name required}"
PKG_VER="${2:?version required}"
IMPORT_SNIPPET="${3:?import snippet required}"

SPEC="${PKG_NAME}==${PKG_VER}"

for attempt in 1 2 3; do
    echo "Attempt ${attempt}: installing ${SPEC} from TestPyPI..."
    if pip install \
        --index-url https://test.pypi.org/simple/ \
        --extra-index-url https://pypi.org/simple/ \
        "${SPEC}"; then
        echo "Install succeeded on attempt ${attempt}"
        break
    fi
    if [ "${attempt}" -lt 3 ]; then
        echo "Install failed; waiting 30s for TestPyPI propagation..."
        sleep 30
    else
        echo "All 3 install attempts failed" >&2
        exit 1
    fi
done

python - <<PY
${IMPORT_SNIPPET}
expected = "${PKG_VER}"
assert v == expected, f"Version mismatch: installed {v!r} != tag {expected!r}"
print(f"{'${PKG_NAME}'} {v} OK")
PY
