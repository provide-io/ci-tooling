#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Fail when branch pins are still declared where they must not be.

A pin that outlives its branch silently keeps a repository on someone's feature
work. This guard runs on the default branch and before a release, so cleanup is
enforced rather than remembered.
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from collections.abc import Sequence
from pathlib import Path


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pins-file", default=".ci/pins.toml")
    return parser.parse_args(list(argv))


def main(argv: Sequence[str]) -> int:
    """Return 1 when any pin is declared, 0 when the tree is clean."""
    args = _parse_args(argv)
    pins_file = Path(args.pins_file)
    if not pins_file.is_file():
        return 0

    declared = tomllib.loads(pins_file.read_text()).get("pin", [])
    if not declared:
        return 0

    packages = ", ".join(entry.get("package", "?") for entry in declared)
    print(
        f"::error::{pins_file} still pins {packages}. Remove the pins before merging or releasing.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
