#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Extract package name from built artifacts."""

import re
import sys
from pathlib import Path


def main() -> None:
    """Extract package name from built artifacts directory."""
    if len(sys.argv) != 2:
        print("Usage: extract_package_name.py <artifacts_path>", file=sys.stderr)
        sys.exit(1)

    artifacts_path = Path(sys.argv[1])

    # Look for wheel or tarball files
    for file_path in artifacts_path.iterdir():
        if file_path.is_file() and (file_path.suffix == ".whl" or file_path.name.endswith(".tar.gz")):
            filename = file_path.name
            match = re.match(r"^([^-]+)", filename)
            if match:
                package_name = match.group(1).replace("_", "-")
                print(package_name)
                return

    print("unknown", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
