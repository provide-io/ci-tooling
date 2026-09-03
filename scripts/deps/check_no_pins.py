#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Fail when branch pins are still declared or still baked into the lockfile.

A pin that outlives its branch silently keeps a repository on someone's feature
work. This guard runs on the default branch and before a release, so cleanup is
enforced rather than remembered.

The lockfile is checked separately from the pins file because clearing the pins
restores pyproject.toml but does not re-lock: uv keeps the overrides under
`[manifest] overrides` until the next resolve, which is long enough to commit
them by accident.
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
    parser.add_argument("--lock-file", default="uv.lock")
    return parser.parse_args(list(argv))


def _declared_pins(pins_file: Path) -> str:
    """Packages named by the pins file, or "" when it declares nothing."""
    if not pins_file.is_file():
        return ""
    declared = tomllib.loads(pins_file.read_text()).get("pin", [])
    return ", ".join(entry.get("package", "?") for entry in declared)


def _locked_overrides(lock_file: Path) -> str:
    """Packages still overridden in the lockfile, or "" when it is clean."""
    if not lock_file.is_file():
        return ""
    overrides = tomllib.loads(lock_file.read_text()).get("manifest", {}).get("overrides", [])
    return ", ".join(entry.get("name", "?") for entry in overrides)


def main(argv: Sequence[str]) -> int:
    """Return 1 when any pin is declared or still locked, 0 when the tree is clean."""
    args = _parse_args(argv)

    pins_file = Path(args.pins_file)
    declared = _declared_pins(pins_file)
    if declared:
        print(
            f"::error::{pins_file} still pins {declared}. Remove the pins before merging or releasing.",
            file=sys.stderr,
        )
        return 1

    lock_file = Path(args.lock_file)
    locked = _locked_overrides(lock_file)
    if locked:
        print(
            f"::error::{lock_file} still overrides {locked}. "
            "Clearing the pins does not re-lock; run `uv lock` and commit the result.",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
