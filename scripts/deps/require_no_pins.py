#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Fail while any pin is active, so a pull request cannot merge on one.

A pin exists to let a branch be *tested* against unreleased code, not to make it
mergeable. Merging while pinned puts the default branch on a dependency that is
not published: the pin does not travel with the merge, so main would resolve from
the registry and get whatever the pin was compensating for.

This runs as its own job so the distinction stays visible. The tests still go
green against the pinned dependency -- that is the point of pinning -- while this
one check stays red until the pin is gone. Make it a required check in branch
protection and the pull request cannot merge until the dependency ships.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pins-json", default="[]")
    return parser.parse_args(list(argv))


def main(argv: Sequence[str]) -> int:
    """Return 1 while any pin is active, 0 when none are."""
    args = _parse_args(argv)
    pins = json.loads(args.pins_json)
    if not pins:
        print("no active pins — this branch resolves entirely from the registry")
        return 0

    print(
        f"::error::{len(pins)} active pin(s); this branch is not mergeable yet.",
        file=sys.stderr,
    )
    for pin in pins:
        print(f"::error::  {pin['package']} -> {pin['url']}  (from {pin['layer']})", file=sys.stderr)
    print(
        "::error::A pin is not carried by the merge. Land the dependency upstream, "
        "release it, then remove the pin.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
