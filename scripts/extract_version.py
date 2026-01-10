#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Extract version from built packages."""

import re
import sys
from pathlib import Path


def extract_version_from_wheel(wheel_path: str) -> str:
    """Extract version from wheel filename."""
    filename = Path(wheel_path).name
    match = re.search(r"-([0-9]+\.[0-9]+\.[0-9]+.*?)-", filename)
    return match.group(1) if match else "0.0.0"


def extract_version_from_tarball(tarball_path: str) -> str:
    """Extract version from tarball filename."""
    filename = Path(tarball_path).name
    match = re.search(r"-([0-9]+\.[0-9]+\.[0-9]+.*?)\.tar\.gz", filename)
    return match.group(1) if match else "0.0.0"


def main() -> None:
    """Extract version from built packages in artifacts directory."""
    if len(sys.argv) != 2:
        print("Usage: extract_version.py <artifacts_path>", file=sys.stderr)
        sys.exit(1)

    artifacts_path = Path(sys.argv[1])

    # Look for wheel files first
    wheel_files = list(artifacts_path.glob("*.whl"))
    if wheel_files:
        version = extract_version_from_wheel(str(wheel_files[0]))
        print(version)
        return

    # Fall back to tarball files
    tarball_files = list(artifacts_path.glob("*.tar.gz"))
    if tarball_files:
        version = extract_version_from_tarball(str(tarball_files[0]))
        print(version)
        return

    print(f"❌ No packages found in {artifacts_path}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
